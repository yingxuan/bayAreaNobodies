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
    normalize_url, fetch_article, compute_content_hash, extract_entities, is_valid_content_url,
    detect_platform, extract_food_entities
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
            # Fallback to fetched_at or use current time
            if article.fetched_at:
                age_hours = (now - article.fetched_at).total_seconds() / 3600
            else:
                age_hours = 0  # Brand new, maximum freshness
    else:
        # Use fetched_at or current time as fallback
        if article.fetched_at:
            age_hours = (now - article.fetched_at).total_seconds() / 3600
        else:
            age_hours = 0  # Brand new, maximum freshness
    
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
    from app.services.google_search import check_budget_exceeded
    
    lock_key = get_lock_key("search_query", query_obj.id)
    if not acquire_lock(lock_key):
        print(f"Query {query_obj.id} already running, skipping")
        return
    
    try:
        # Check budget before processing
        if check_budget_exceeded():
            print(f"WARNING: Daily CSE budget exceeded. Skipping query {query_obj.id}: {query_obj.query}")
            return
        
        print(f"Processing query {query_obj.id}: {query_obj.query}")
        
        # Fetch search results
        # Use 24-hour look back window for all queries
        date_restrict = "d1"
        results = fetch_multiple_pages(
            query=query_obj.query,
            site_domain=query_obj.site_domain,
            max_results=30,
            date_restrict=date_restrict
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
            
            # Skip invalid URLs (homepage/explore pages)
            if not is_valid_content_url(url):
                print(f"Skipping {url}: invalid content URL (homepage/explore page)")
                continue
            
            # For food_radar, skip Blind URLs (we allow 1point3acres.com and huaren.us for food content)
            if query_obj.source_type == "food_radar":
                if "teamblind.com" in url.lower():
                    print(f"Skipping {url}: Blind content not allowed in food_radar")
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
            
            # Detect platform from URL (for food_radar and future use)
            platform = detect_platform(url)
            
            # Extract video ID and thumbnail URL
            from app.services.article_fetcher import extract_video_id, extract_thumbnail_url
            video_id = extract_video_id(url, platform)
            thumbnail_url = extract_thumbnail_url(url, platform, video_id)
            
            # Fetch article content
            text, title, published_at = fetch_article(url)
            
            # Graceful fallback: if extraction fails, use Google snippet and title
            # This is important for platforms like YouTube/TikTok that may not extract well
            if not text or len(text) < 100:
                # Fallback to Google snippet if available
                snippet = item.get("snippet", "")
                if snippet and len(snippet) > 50:
                    text = snippet
                    print(f"Using Google snippet for {url} (extraction failed)")
                else:
                    print(f"Skipping {url}: insufficient content and no snippet")
                    continue
            
            # Use title from fetch or fallback to Google result title
            final_title = title or item.get("title", "")
            if not final_title:
                print(f"Skipping {url}: no title available")
                continue
            
            # Check for login-required content (common patterns in Chinese sites)
            # Only check if we have substantial text (not just snippet)
            if len(text) > 500:
                login_indicators = ['您需要 登录', '需要 登录', '没有帐号', '登录 才可以']
                if any(indicator in text for indicator in login_indicators):
                    # If login prompt is a significant portion, skip
                    if sum(len(ind) for ind in login_indicators if ind in text) > len(text) * 0.2:
                        print(f"Skipping {url}: login-required page")
                        continue
            
            # Compute content hash for deduplication
            content_hash = compute_content_hash(final_title, text)
            
            # Check for duplicate by content hash
            duplicate = db.query(Article).filter(
                Article.content_hash == content_hash
            ).first()
            
            if duplicate:
                print(f"Skipping {url}: duplicate content")
                continue
            
            # Summarize (works with snippet or full text)
            summary, bullets = summarize_article(text, final_title)
            
            # Extract entities based on source type
            # For food_radar, use food-focused extraction; otherwise use general extraction
            if query_obj.source_type == "food_radar":
                cities, food_tags, general_tags, place_name = extract_food_entities(text, final_title)
                # Store place_name in tags if found (we don't have a separate field)
                all_tags = food_tags + general_tags
                if place_name:
                    all_tags.append(f"place:{place_name}")
                companies = []  # Not relevant for food content
            else:
                companies, cities, tags = extract_entities(text, final_title)
                all_tags = tags
                place_name = None
            
            # Create article
            from datetime import datetime as dt
            import pytz
            article = Article(
                url=url,
                normalized_url=normalized,
                title=final_title,
                cleaned_text=text[:50000],  # Limit size
                content_hash=content_hash,
                source_type=query_obj.source_type,
                platform=platform,  # Store detected platform
                video_id=video_id,  # Store video ID for embedding
                thumbnail_url=thumbnail_url,  # Store thumbnail URL
                published_at=published_at,
                fetched_at=dt.now(pytz.UTC),  # Explicitly set fetched_at
                summary=summary,
                summary_bullets=bullets,
                company_tags=json.dumps(companies) if companies else None,
                city_hints=json.dumps(cities) if cities else None,
                tags=json.dumps(all_tags) if all_tags else None
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
    from app.services.google_search import check_budget_exceeded
    
    db = SessionLocal()
    try:
        queries = db.query(SourceQuery).filter(SourceQuery.enabled == True).all()
        processed = 0
        skipped = 0
        
        for query in queries:
            # Check budget before each query
            if check_budget_exceeded():
                print(f"WARNING: Daily CSE budget exceeded. Skipping remaining {len(queries) - processed} queries.")
                skipped = len(queries) - processed
                break
            
            process_search_query(query, db)
            processed += 1
        
        print(f"Search jobs completed: {processed} processed, {skipped} skipped due to budget")
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
    """Search for coupons from dealmoon.com, 1point3acres.com, and huaren.us for Bay Area deals"""
    from app.services.google_search import check_budget_exceeded
    
    # Check budget before starting
    if check_budget_exceeded():
        print("WARNING: Daily CSE budget exceeded. Skipping coupon search.")
        return
    
    db = SessionLocal()
    try:
        # Search dealmoon.com, 1point3acres.com, and huaren.us for deals (include community posts)
        queries = [
            "site:dealmoon.com Bay Area coupon deal",
            "site:dealmoon.com Bay Area discount",
            "site:dealmoon.com San Francisco San Jose deal",
            "site:1point3acres.com Bay Area coupon deal",
            "site:1point3acres.com 湾区 优惠 折扣",
            "site:huaren.us Bay Area coupon deal",
            "site:huaren.us 湾区 优惠 折扣",
        ]
        
        processed_count = 0
        for query in queries:
            # Check budget before each query
            if check_budget_exceeded():
                print(f"WARNING: Budget exceeded during coupon search. Processed {processed_count} queries.")
                break
            
            # Use 24-hour lookback for deals
            results = search_google(query, num=10, date_restrict="d1")
            
            # Check if error occurred
            if results.get("error"):
                print(f"Error in query '{query}': {results.get('error')}")
                continue
            
            items = results.get("items", [])
            processed_count += 1
            
            for item in items:
                url = item.get("link", "")
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                
                # Google CSE sometimes includes pagemap with image info
                pagemap = item.get("pagemap", {})
                
                # Accept URLs from dealmoon.com, 1point3acres.com, or huaren.us
                if not url or not any(domain in url for domain in ["dealmoon.com", "1point3acres.com", "huaren.us"]):
                    continue
                
                # Simple extraction of coupon info
                from app.models import Coupon
                
                # Check if already exists
                existing = db.query(Coupon).filter(
                    Coupon.source_url == url
                ).first()
                
                if existing:
                    continue
                
                # Extract city from title/snippet
                cities = [
                    "Sunnyvale", "Cupertino", "San Jose", "Palo Alto", "Mountain View",
                    "San Francisco", "SF", "Oakland", "Fremont", "Santa Clara",
                    "Redwood City", "Menlo Park", "Foster City", "San Mateo"
                ]
                city = None
                for c in cities:
                    if c.lower() in (title + snippet).lower():
                        city = c
                        break
                
                # Extract category
                category = None
                text_lower = (title + snippet).lower()
                if "boba" in text_lower or "奶茶" in text_lower or "milk tea" in text_lower:
                    category = "boba"
                elif "restaurant" in text_lower or "dining" in text_lower or "food" in text_lower:
                    category = "food"
                elif "cafe" in text_lower or "coffee" in text_lower:
                    category = "cafe"
                elif "dessert" in text_lower or "bakery" in text_lower:
                    category = "dessert"
                elif "shopping" in text_lower or "store" in text_lower or "retail" in text_lower:
                    category = "shopping"
                elif "travel" in text_lower or "hotel" in text_lower or "flight" in text_lower:
                    category = "travel"
                elif "tech" in text_lower or "electronics" in text_lower or "gadget" in text_lower:
                    category = "tech"
                else:
                    category = "general"  # Default to general
                
                # Try to extract coupon code from snippet
                code = None
                import re
                # Look for patterns like "CODE: ABC123" or "Code: XYZ" or "优惠码: ABC"
                code_patterns = [
                    r'(?:code|优惠码|promo code|coupon code)[:\s]+([A-Z0-9]{4,20})',
                    r'([A-Z0-9]{4,20})(?:\s+code|\s+coupon)',
                ]
                for pattern in code_patterns:
                    match = re.search(pattern, snippet, re.IGNORECASE)
                    if match:
                        code = match.group(1).strip()
                        break
                
                # Extract image and video URLs
                from app.services.coupon_extractor import extract_media_from_snippet
                
                image_url = None
                video_url = None
                
                # Try to extract from Google's pagemap first (most reliable)
                if pagemap:
                    # Google includes cse_image with actual deal images
                    cse_images = pagemap.get("cse_image", [])
                    if cse_images and isinstance(cse_images, list) and len(cse_images) > 0:
                        img_data = cse_images[0]
                        image_url = img_data.get("src") or img_data.get("url")
                    
                    # Also check metatags for og:image (fallback)
                    if not image_url:
                        metatags = pagemap.get("metatags", [])
                        if metatags and isinstance(metatags, list) and len(metatags) > 0:
                            meta = metatags[0]
                            image_url = meta.get("og:image") or meta.get("twitter:image")
                    
                    # Check for video information
                    videoobject = pagemap.get("videoobject", [])
                    if videoobject and isinstance(videoobject, list) and len(videoobject) > 0:
                        video_data = videoobject[0]
                        video_url = video_data.get("embedurl") or video_data.get("contenturl")
                
                # Quick extraction from snippet (for YouTube links, etc.)
                if not video_url:
                    snippet_image, snippet_video = extract_media_from_snippet(snippet, url)
                    if snippet_video:
                        video_url = snippet_video
                    # Only use snippet image if no pagemap image found
                    if not image_url and snippet_image:
                        image_url = snippet_image
                
                # Calculate confidence based on how much info we have
                confidence = 0.5
                if code:
                    confidence += 0.2
                if city:
                    confidence += 0.1
                if category:
                    confidence += 0.1
                if len(snippet) > 100:
                    confidence += 0.1
                if image_url or video_url:
                    confidence += 0.1  # Bonus for having media
                
                coupon = Coupon(
                    title=title,
                    code=code,
                    source_url=url,
                    image_url=image_url,
                    video_url=video_url,
                    city=city,
                    category=category,
                    terms=snippet[:500],  # Limit terms length
                    confidence=min(confidence, 1.0)
                )
                db.add(coupon)
        
        db.commit()
        print(f"Coupon search completed: processed {processed_count}/{len(queries)} queries")
    except Exception as e:
        print(f"Error in coupon search: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def run_deals_search():
    """Search for deals (bank/credit card/brokerage/life) using Google CSE"""
    from app.services.deals_service import search_and_store_deals
    
    db = SessionLocal()
    try:
        processed, skipped, quota_exceeded = search_and_store_deals(db)
        if quota_exceeded:
            print(f"Deals search completed: {processed} processed, {skipped} skipped due to quota")
        else:
            print(f"Deals search completed: {processed} queries processed")
    except Exception as e:
        print(f"Error in deals search: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def run_gossip_search():
    """Search for gossip content using Google CSE"""
    from app.services.gossip_service import search_and_store_gossip
    
    db = SessionLocal()
    try:
        processed, skipped, quota_exceeded = search_and_store_gossip(db)
        if quota_exceeded:
            print(f"Gossip search completed: {processed} processed, {skipped} skipped due to quota")
        else:
            print(f"Gossip search completed: {processed} queries processed")
    except Exception as e:
        print(f"Error in gossip search: {e}")
        import traceback
        traceback.print_exc()
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
            for source_type in ["di_li", "blind"]:
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
    # Search jobs: run daily at 2 AM with 24-hour look back window
    scheduler.add_job(
        run_search_jobs,
        trigger=CronTrigger(hour=2, minute=0),
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
    
    # Deals search: 2x per day (8 AM and 2 PM)
    scheduler.add_job(
        run_deals_search,
        trigger=CronTrigger(hour=8, minute=0),
        id="deals_search_morning",
        replace_existing=True
    )
    
    scheduler.add_job(
        run_deals_search,
        trigger=CronTrigger(hour=14, minute=0),
        id="deals_search_afternoon",
        replace_existing=True
    )
    
    # Gossip search: 2x per day (9 AM and 3 PM)
    scheduler.add_job(
        run_gossip_search,
        trigger=CronTrigger(hour=9, minute=0),
        id="gossip_search_morning",
        replace_existing=True
    )
    
    scheduler.add_job(
        run_gossip_search,
        trigger=CronTrigger(hour=15, minute=0),
        id="gossip_search_afternoon",
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

