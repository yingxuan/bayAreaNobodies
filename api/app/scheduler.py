import os
import redis
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import pytz
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import SourceQuery, SearchResultRaw, Article, TrendingSnapshot
from app.services.google_search import search_google, fetch_multiple_pages
from app.services.article_fetcher import (
    normalize_url, fetch_article, compute_content_hash, extract_entities
)
from app.services.summarizer import summarize_article
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

scheduler = BackgroundScheduler(timezone=pytz.timezone('America/Los_Angeles'))


def get_lock_key(job_name: str, *args) -> str:
    """Generate lock key for distributed locking"""
    key_parts = [job_name] + [str(a) for a in args]
    return f"lock:{':'.join(key_parts)}"


def acquire_lock(lock_key: str, timeout: int = 300) -> bool:
    """Acquire distributed lock using Redis"""
    if not redis_client:
        return True  # No Redis, assume single instance
    
    return redis_client.set(lock_key, "1", nx=True, ex=timeout)


def release_lock(lock_key: str):
    """Release distributed lock"""
    if redis_client:
        redis_client.delete(lock_key)


def calculate_scores(article: Article, search_rank: int, max_rank: int = 100):
    """Calculate freshness, search rank, and final scores"""
    # Search rank score (inverse of rank, normalized)
    article.search_rank_score = max(0, (max_rank - search_rank) / max_rank)
    
    # Freshness score (based on published_at or fetched_at)
    now = datetime.now(pytz.UTC)
    if article.published_at:
        # Ensure published_at is a timezone-aware datetime object
        pub_date = article.published_at
        if isinstance(pub_date, str):
            from dateutil import parser
            try:
                pub_date = parser.parse(pub_date)
            except:
                pub_date = None
        if pub_date:
            # Make timezone-aware if naive
            if pub_date.tzinfo is None:
                pub_date = pytz.UTC.localize(pub_date)
            age_hours = (now - pub_date).total_seconds() / 3600
        else:
            age_hours = (now - article.fetched_at).total_seconds() / 3600
    else:
        age_hours = (now - article.fetched_at).total_seconds() / 3600
    
    # Freshness decays over time (max score for < 24h, decays to 0 at 14 days)
    if age_hours < 24:
        article.freshness_score = 1.0
    elif age_hours < 336:  # 14 days
        article.freshness_score = max(0, 1.0 - (age_hours - 24) / 312)
    else:
        article.freshness_score = 0.0
    
    # Engagement score (already set, but ensure it's initialized)
    if article.engagement_score is None:
        article.engagement_score = 0.0
    
    # Final score
    article.final_score = (
        0.45 * article.search_rank_score +
        0.35 * article.freshness_score +
        0.20 * article.engagement_score
    )


def process_search_query(query_obj: SourceQuery, db: Session):
    """Process a single search query and fetch articles"""
    lock_key = get_lock_key("search_query", query_obj.id)
    if not acquire_lock(lock_key):
        print(f"Query {query_obj.id} already running, skipping")
        return
    
    try:
        print(f"Processing query {query_obj.id}: {query_obj.query}")
        
        # Fetch search results
        results = fetch_multiple_pages(
            query=query_obj.query,
            site_domain=query_obj.site_domain,
            max_results=30,
            date_restrict="d14"  # Last 14 days
        )
        
        if not results:
            print(f"No results for query {query_obj.id}")
            return
        
        # Store raw results
        for idx, item in enumerate(results, 1):
            raw_result = SearchResultRaw(
                query_id=query_obj.id,
                url=item.get("link", ""),
                title=item.get("title"),
                snippet=item.get("snippet"),
                raw_json=json.dumps(item),
                search_rank=idx
            )
            db.add(raw_result)
        
        db.commit()
        
        # Process each result URL
        for idx, item in enumerate(results, 1):
            url = item.get("link", "")
            if not url:
                continue
            
            normalized = normalize_url(url)
            
            # Check if article already exists
            existing = db.query(Article).filter(
                Article.normalized_url == normalized
            ).first()
            
            if existing:
                # Update scores if needed
                calculate_scores(existing, idx)
                db.commit()
                continue
            
            # Fetch article content
            text, title, published_at = fetch_article(url)
            
            if not text or len(text) < 100:
                print(f"Skipping {url}: insufficient content")
                continue
            
            # Check for login-required content (common patterns in Chinese sites)
            login_indicators = ['您需要 登录', '需要 登录', '没有帐号', '登录 才可以']
            if any(indicator in text for indicator in login_indicators):
                # If login prompt is a significant portion, skip
                if len(text) < 500 or sum(len(ind) for ind in login_indicators if ind in text) > len(text) * 0.2:
                    print(f"Skipping {url}: login-required page")
                    continue
            
            # Compute content hash for deduplication
            content_hash = compute_content_hash(title, text)
            
            # Check for duplicate by content hash
            duplicate = db.query(Article).filter(
                Article.content_hash == content_hash
            ).first()
            
            if duplicate:
                print(f"Skipping {url}: duplicate content")
                continue
            
            # Summarize
            summary, bullets = summarize_article(text, title)
            
            # Extract entities
            companies, cities, tags = extract_entities(text, title)
            
            # Create article
            article = Article(
                url=url,
                normalized_url=normalized,
                title=title or item.get("title", ""),
                cleaned_text=text[:50000],  # Limit size
                content_hash=content_hash,
                source_type=query_obj.source_type,
                published_at=published_at,
                summary=summary,
                summary_bullets=bullets,
                company_tags=json.dumps(companies) if companies else None,
                city_hints=json.dumps(cities) if cities else None,
                tags=json.dumps(tags) if tags else None
            )
            
            # Calculate scores
            calculate_scores(article, idx)
            
            db.add(article)
            db.commit()
            print(f"Added article: {title}")
        
    except Exception as e:
        print(f"Error processing query {query_obj.id}: {e}")
        db.rollback()
    finally:
        release_lock(lock_key)


def run_search_jobs():
    """Run all enabled search queries"""
    db = SessionLocal()
    try:
        queries = db.query(SourceQuery).filter(SourceQuery.enabled == True).all()
        for query in queries:
            process_search_query(query, db)
    finally:
        db.close()


def create_trending_snapshots():
    """Create trending snapshots for each source type"""
    db = SessionLocal()
    try:
        from app.models import SourceType
        
        for source_type in SourceType:
            # Get top 20 articles by score
            articles = db.query(Article).filter(
                Article.source_type == source_type.value,
                Article.final_score > 0
            ).order_by(Article.final_score.desc()).limit(20).all()
            
            # Clear old snapshots for this source (keep only latest)
            db.query(TrendingSnapshot).filter(
                TrendingSnapshot.source_type == source_type.value
            ).delete()
            
            # Create new snapshots
            for rank, article in enumerate(articles, 1):
                snapshot = TrendingSnapshot(
                    source_type=source_type.value,
                    article_id=article.id,
                    rank=rank
                )
                db.add(snapshot)
            
            db.commit()
            print(f"Created trending snapshot for {source_type.value}")
    except Exception as e:
        print(f"Error creating trending snapshots: {e}")
        db.rollback()
    finally:
        db.close()


def run_coupon_search():
    """Search for coupons using Google Search"""
    db = SessionLocal()
    try:
        queries = [
            "coupon Sunnyvale boba",
            "BOGO Bay Area",
            "discount Cupertino restaurant",
            "coupon San Jose food"
        ]
        
        for query in queries:
            results = search_google(query, num=10, date_restrict="d14")
            items = results.get("items", [])
            
            for item in items:
                url = item.get("link", "")
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                
                # Simple extraction of coupon info
                # In production, use more sophisticated parsing
                from app.models import Coupon
                
                # Check if already exists
                existing = db.query(Coupon).filter(
                    Coupon.source_url == url
                ).first()
                
                if existing:
                    continue
                
                # Extract city from title/snippet
                cities = ["Sunnyvale", "Cupertino", "San Jose", "Palo Alto", "Mountain View"]
                city = None
                for c in cities:
                    if c.lower() in (title + snippet).lower():
                        city = c
                        break
                
                # Extract category
                category = None
                if "boba" in query.lower() or "奶茶" in (title + snippet).lower():
                    category = "boba"
                elif "food" in query.lower() or "restaurant" in query.lower():
                    category = "food"
                
                coupon = Coupon(
                    title=title,
                    code=None,  # Would need parsing
                    source_url=url,
                    city=city,
                    category=category,
                    terms=snippet,
                    confidence=0.5
                )
                db.add(coupon)
        
        db.commit()
        print("Coupon search completed")
    except Exception as e:
        print(f"Error in coupon search: {e}")
        db.rollback()
    finally:
        db.close()


def generate_digests():
    """Generate daily digests for all users"""
    db = SessionLocal()
    try:
        from app.models import User, Digest, TrendingSnapshot, Article, Coupon, Holding
        from app.services.stock_service import get_stock_price
        from datetime import datetime, date
        
        users = db.query(User).all()
        
        for user in users:
            # Get portfolio summary
            holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
            portfolio_data = {
                "total_cost": sum(h.cost_basis for h in holdings),
                "holdings": []
            }
            
            total_value = 0.0
            for holding in holdings:
                try:
                    price = get_stock_price(holding.ticker)
                    value = price * holding.quantity
                    total_value += value
                    portfolio_data["holdings"].append({
                        "ticker": holding.ticker,
                        "quantity": holding.quantity,
                        "cost_basis": holding.cost_basis,
                        "value": value,
                        "pnl": value - holding.cost_basis
                    })
                except:
                    pass
            
            portfolio_data["total_value"] = total_value
            portfolio_data["total_pnl"] = total_value - portfolio_data["total_cost"]
            
            # Get trending items
            trending_data = {}
            for source_type in ["di_li", "blind", "xhs"]:
                snapshots = db.query(TrendingSnapshot).filter(
                    TrendingSnapshot.source_type == source_type
                ).order_by(TrendingSnapshot.rank).limit(5).all()
                
                trending_data[source_type] = [
                    {
                        "id": s.article.id,
                        "title": s.article.title,
                        "summary": s.article.summary,
                        "url": s.article.url
                    }
                    for s in snapshots
                ]
            
            # Get coupons
            city = user.preferred_city or "Sunnyvale"
            coupons = db.query(Coupon).filter(
                Coupon.city.ilike(f"%{city}%")
            ).order_by(Coupon.confidence.desc()).limit(5).all()
            
            coupon_data = [
                {
                    "id": c.id,
                    "title": c.title,
                    "code": c.code,
                    "source_url": c.source_url
                }
                for c in coupons
            ]
            
            # Create digest
            digest_content = {
                "portfolio": portfolio_data,
                "trending": trending_data,
                "coupons": coupon_data,
                "generated_at": datetime.now().isoformat()
            }
            
            digest = Digest(
                user_id=user.id,
                digest_date=datetime.now(),
                content_json=json.dumps(digest_content)
            )
            db.add(digest)
        
        db.commit()
        print(f"Generated digests for {len(users)} users")
    except Exception as e:
        print(f"Error generating digests: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    # Search jobs: run every hour for queries with interval_min=60
    scheduler.add_job(
        run_search_jobs,
        trigger=IntervalTrigger(minutes=60),
        id="search_jobs",
        replace_existing=True
    )
    
    # Trending snapshots: every hour
    scheduler.add_job(
        create_trending_snapshots,
        trigger=IntervalTrigger(minutes=60),
        id="trending_snapshots",
        replace_existing=True
    )
    
    # Coupon search: daily at 6 AM
    scheduler.add_job(
        run_coupon_search,
        trigger=CronTrigger(hour=6, minute=0),
        id="coupon_search",
        replace_existing=True
    )
    
    # Digests: 8:30 AM and 4:30 PM
    scheduler.add_job(
        generate_digests,
        trigger=CronTrigger(hour=8, minute=30),
        id="digest_morning",
        replace_existing=True
    )
    
    scheduler.add_job(
        generate_digests,
        trigger=CronTrigger(hour=16, minute=30),
        id="digest_evening",
        replace_existing=True
    )
    
    scheduler.start()
    print("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    scheduler.shutdown()

