"""
Unified feed endpoints for the 4 main feeds:
1. 美食 (Food) - food content from YouTube, Instagram, TikTok
2. 羊毛 (Deals) - food coupons and discounts
3. 暴富 (Wealth) - stock prices and news
4. 八卦 (Gossip) - trending posts from 1point3acres and Teamblind
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from app.database import get_db
from app.models import Article, Coupon
from app.schemas import (
    ArticleResponse, CouponResponse, FoodRadarFeedResponse,
    DealsFeedResponse, WealthFeedResponse, GossipFeedResponse
)
from typing import Optional, List, Dict
from datetime import datetime, timezone
import json

router = APIRouter()


@router.get("/food", response_model=FoodRadarFeedResponse)
def get_food_feed(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get "美食" (Food) feed - local Chinese food in Bay Area
    ONLY shows:
    1. Popular YouTube Chinese food bloggers (热门中文探店博主)
    2. Popular food posts from huaren.us or 1point3acres.com in San Francisco Bay Area (旧金山湾区)
    """
    import re
    import json
    
    # Helper function to detect Chinese characters
    def has_chinese(text: str) -> bool:
        if not text:
            return False
        # Check for Chinese characters (CJK Unified Ideographs)
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        return bool(chinese_pattern.search(text))
    
    # Helper function to check if article is about Bay Area
    def is_bay_area_related(article: Article) -> bool:
        """Check if article is related to San Francisco Bay Area"""
        bay_area_cities = [
            'sunnyvale', 'cupertino', 'san jose', 'palo alto', 'mountain view',
            'fremont', 'santa clara', 'redwood city', 'menlo park', 'foster city',
            'san mateo', 'burlingame', 'millbrae', 'san francisco', 'sf', 'oakland',
            'berkeley', 'alameda', 'hayward', 'union city', 'newark', '湾区', 'bay area'
        ]
        
        # Check title and summary
        title_text = (article.title or "").lower()
        summary_text = (article.summary or "").lower()
        full_text = (title_text + " " + summary_text)
        
        # Check city_hints
        if article.city_hints:
            try:
                cities = json.loads(article.city_hints)
                if isinstance(cities, list):
                    for city in cities:
                        if any(bay_city in str(city).lower() for bay_city in bay_area_cities):
                            return True
            except:
                pass
        
        # Check if any Bay Area city is mentioned in title or summary
        return any(bay_city in full_text for bay_city in bay_area_cities)
    
    # Helper function to check if article is popular
    def is_popular(article: Article) -> bool:
        """Check if article is popular based on engagement metrics"""
        # For YouTube: consider popular if:
        # - views > 1000 OR
        # - engagement_score > 10 OR
        # - final_score > 0.3 (top 30%)
        if 'youtube.com' in article.url.lower():
            return (article.views or 0) > 1000 or (article.engagement_score or 0) > 10 or (article.final_score or 0) > 0.3
        
        # For huaren/1point3acres: consider popular if:
        # - views > 50 OR
        # - engagement_score > 5 OR
        # - final_score > 0.25
        return (article.views or 0) > 50 or (article.engagement_score or 0) > 5 or (article.final_score or 0) > 0.25
    
    # Base query: food_radar articles from allowed sources
    base_query = db.query(Article).filter(
        Article.source_type == "food_radar",
        (
            Article.url.ilike('%youtube.com%') |
            Article.url.ilike('%1point3acres.com%') |
            Article.url.ilike('%huaren.us%')
        )
    )
    
    # Filter articles
    articles = base_query.all()
    filtered_articles = []
    
    for article in articles:
        # For YouTube: must be Chinese AND popular
        if 'youtube.com' in article.url.lower():
            title_text = (article.title or "")
            summary_text = (article.summary or "")
            if has_chinese(title_text) or has_chinese(summary_text):
                if is_popular(article):
                    filtered_articles.append(article)
        # For 1point3acres.com and huaren.us: must be Bay Area related AND popular
        elif '1point3acres.com' in article.url.lower() or 'huaren.us' in article.url.lower():
            if is_bay_area_related(article) and is_popular(article):
                filtered_articles.append(article)
    
    # Sort manually: prioritize videos, then by freshness and relevance
    filtered_articles.sort(
        key=lambda a: (
            0 if (a.video_id is not None) else 1,  # Videos first
            0 if (a.thumbnail_url is not None) else 1,  # Then thumbnails
            -(a.fetched_at.timestamp() if a.fetched_at else 0),  # Most recent first
            -(a.final_score or 0)  # Highest score first
        )
    )
    
    # Limit results
    articles = filtered_articles[:limit]
    
    # Convert to response format
    article_responses = []
    for article in articles:
        # Parse tags to extract place name if present
        tags_list = []
        place_name = None
        if article.tags:
            try:
                tags_list = json.loads(article.tags)
                for tag in tags_list:
                    if isinstance(tag, str) and tag.startswith("place:"):
                        place_name = tag.replace("place:", "").strip()
                        tags_list = [t for t in tags_list if not (isinstance(t, str) and t.startswith("place:"))]
                        break
            except:
                pass
        
        article_dict = {
            "id": article.id,
            "url": article.url,
            "title": article.title,
            "summary": article.summary,
            "summary_bullets": article.summary_bullets,
            "tags": json.dumps(tags_list) if tags_list else article.tags,
            "city_hints": article.city_hints,
            "company_tags": article.company_tags,
            "source_type": article.source_type,
            "platform": article.platform,
            "video_id": article.video_id,
            "thumbnail_url": article.thumbnail_url,
            "place_name": place_name,
            "published_at": article.published_at,
            "views": article.views,
            "saves": article.saves,
            "final_score": article.final_score
        }
        article_responses.append(ArticleResponse(**article_dict))
    
    return FoodRadarFeedResponse(
        articles=article_responses,
        total=len(article_responses),
        filters={}
    )


@router.get("/deals", response_model=DealsFeedResponse)
def get_deals_feed(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get "羊毛" (Deals) feed - all coupons and discounts in Bay Area
    Blends all coupons, ranked by score (relevance for 北美华人) and freshness
    """
    from app.services.deals_service import check_deals_budget_exceeded, get_deals_usage_key
    import os
    import redis
    
    # Query: prioritize scored deals (auto-discovered), fallback to legacy coupons
    # Only show deals from 1point3acres.com, huaren.us, and dealmoon.com (exclude YouTube)
    query_scored = db.query(Coupon).filter(
        Coupon.score > 0,
        Coupon.canonical_url.isnot(None),
        ~Coupon.source_url.ilike('%youtube.com%'),  # Exclude YouTube
        ~Coupon.source_url.ilike('%youtu.be%'),  # Exclude YouTube short links
        (
            Coupon.source_url.ilike('%1point3acres.com%') |
            Coupon.source_url.ilike('%huaren.us%') |
            Coupon.source_url.ilike('%dealmoon.com%') |
            Coupon.source.ilike('%1point3acres.com%') |
            Coupon.source.ilike('%huaren.us%') |
            Coupon.source.ilike('%dealmoon.com%')
        )
    )
    
    query_legacy = db.query(Coupon).filter(
        (
            Coupon.source_url.ilike('%dealmoon.com%') |
            Coupon.source_url.ilike('%1point3acres.com%') |
            Coupon.source_url.ilike('%huaren.us%')
        ),
        ~Coupon.source_url.ilike('%youtube.com%'),  # Exclude YouTube
        ~Coupon.source_url.ilike('%youtu.be%'),  # Exclude YouTube short links
        (Coupon.score.is_(None) | (Coupon.score == 0))  # Legacy entries
    )
    
    # Get scored deals first (ranked by score)
    # Priority: food_fast and retail_family first, then others
    from sqlalchemy import case
    
    # Create priority score: food_fast=3, retail_family=2, others=1
    category_priority = case(
        (Coupon.category == 'food_fast', 3),
        (Coupon.category == 'retail_family', 2),
        else_=1
    )
    
    scored_coupons = query_scored.order_by(
        desc(category_priority),  # Priority categories first
        desc(Coupon.score),
        desc(Coupon.fetched_at)
    ).limit(limit).all()
    
    # Fill remaining slots with legacy coupons if needed
    remaining = limit - len(scored_coupons)
    legacy_coupons = []
    if remaining > 0:
        legacy_coupons = query_legacy.order_by(
            desc(Coupon.confidence),
            desc(Coupon.created_at)
        ).limit(remaining).all()
    
    all_coupons = list(scored_coupons) + list(legacy_coupons)
    
    # Check data freshness
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None
    quota_exceeded = check_deals_budget_exceeded()
    data_freshness = "stale_due_to_quota" if quota_exceeded else "fresh"
    
    # Get usage info if available
    usage_info = None
    if redis_client:
        usage_key = get_deals_usage_key()
        current_usage = redis_client.get(usage_key)
        if current_usage:
            try:
                usage_info = {
                    "current_usage": int(current_usage),
                    "daily_budget": int(os.getenv("DEALS_CSE_DAILY_BUDGET", "80"))
                }
            except:
                pass
    
    return DealsFeedResponse(
        coupons=[CouponResponse.model_validate(c) for c in all_coupons],
        total=len(all_coupons),
        data_freshness=data_freshness,
        usage_info=usage_info,
        filters={}
    )


@router.get("/wealth", response_model=WealthFeedResponse)
def get_wealth_feed(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get "暴富" (Wealth) feed - latest YouTube videos from US stock investment bloggers
    Only shows videos related to "美股" (US stocks)
    Prioritizes specific bloggers: 视野环球财经, 美投讲美股, 美投侃新闻, 股市咖啡屋 Stock Cafe, 老李玩钱
    """
    from datetime import timedelta
    import pytz
    
    # Preferred bloggers (in priority order) - 美股博主优先
    PREFERRED_BLOGGERS = [
        "美投讲美股",  # 明确提到"美股"的博主最高优先级
        "美投侃新闻",
        "视野环球财经",
        "股市咖啡屋 Stock Cafe",
        "股市咖啡屋",
        "老李玩钱"
    ]
    
    # US stock related keywords (must contain at least one)
    US_STOCK_KEYWORDS = [
        "美股", "us stock", "us stocks", "美国股票", "美国股市",
        "nasdaq", "spy", "qqq", "dow", "s&p 500", "s&p500",
        "aapl", "msft", "googl", "amzn", "meta", "tsla", "nvda",
        "英伟达", "苹果", "微软", "特斯拉", "亚马逊", "meta",
        "投资", "股票", "股市", "投资组合", "portfolio"
    ]
    
    # Hong Kong stock keywords to EXCLUDE
    HK_STOCK_KEYWORDS = [
        "港股", "hong kong stock", "hk stock", "香港股票", "香港股市",
        "恒生", "hsi", "hang seng", "腾讯", "tencent", "阿里巴巴", "alibaba",
        "美团", "meituan", "小米", "xiaomi", "京东", "jd.com",
        "港股通", "h股", "红筹", "中概股"  # 中概股可能包含港股，但先排除明显港股
    ]
    
    # Only show wealth articles from youtube.com, published in the last 5 days
    cutoff_time = datetime.now(pytz.UTC) - timedelta(days=5)
    
    query = db.query(Article).filter(
        Article.source_type == "wealth",
        Article.url.ilike('%youtube.com%'),
        Article.published_at >= cutoff_time
    )
    
    articles = query.all()
    
    # Filter articles: must be related to US stocks and NOT Hong Kong stocks
    def is_us_stock_related(article):
        title = (article.title or "").lower()
        summary = (article.summary or "").lower()
        combined_text = title + " " + summary
        
        # First check: exclude Hong Kong stocks
        for hk_keyword in HK_STOCK_KEYWORDS:
            if hk_keyword.lower() in combined_text:
                return False  # Exclude if contains HK stock keywords
        
        # Second check: must contain US stock keywords
        for keyword in US_STOCK_KEYWORDS:
            if keyword.lower() in combined_text:
                return True
        return False
    
    # Filter to only US stock related articles (excluding HK stocks)
    us_stock_articles = [a for a in articles if is_us_stock_related(a)]
    
    # Separate articles by preferred bloggers (美股博主优先)
    preferred_articles = []
    other_articles = []
    
    # Check if article mentions "美股" explicitly (highest priority)
    def mentions_us_stocks_explicitly(article):
        title = (article.title or "").lower()
        summary = (article.summary or "").lower()
        combined = title + " " + summary
        return "美股" in combined or "us stock" in combined or "us stocks" in combined
    
    for article in us_stock_articles:
        title = (article.title or "").lower()
        summary = (article.summary or "").lower()
        is_preferred = False
        
        # Check if it's from preferred blogger
        for blogger in PREFERRED_BLOGGERS:
            if blogger.lower() in title or blogger.lower() in summary:
                is_preferred = True
                break
        
        if is_preferred:
            preferred_articles.append(article)
        else:
            other_articles.append(article)
    
    # Sort preferred articles by: 1) explicit "美股" mention, 2) blogger priority, 3) freshness
    def get_blogger_priority(article):
        title = (article.title or "").lower()
        summary = (article.summary or "").lower()
        for idx, blogger in enumerate(PREFERRED_BLOGGERS):
            if blogger.lower() in title or blogger.lower() in summary:
                return idx
        return len(PREFERRED_BLOGGERS)
    
    # Boost articles that explicitly mention "美股"
    def get_us_stock_boost(article):
        if mentions_us_stocks_explicitly(article):
            return 0  # Highest priority
        return 1  # Lower priority
    
    preferred_articles.sort(
        key=lambda a: (
            get_us_stock_boost(a),  # Explicit "美股" mention first
            get_blogger_priority(a),  # Then by blogger priority
            -(a.published_at.timestamp() if a.published_at else 0)  # Then by freshness
        )
    )
    
    # Sort other articles: explicit "美股" mention first, then freshness and score
    other_articles.sort(
        key=lambda a: (
            get_us_stock_boost(a),  # Explicit "美股" mention first
            -(a.published_at.timestamp() if a.published_at else 0),  # Then freshness
            -(a.final_score or 0)  # Then score
        )
    )
    
    # Only return preferred bloggers (美股财经博主)
    # Do not include other_articles - only show videos from specified bloggers
    articles = preferred_articles[:limit]
    
    # Convert to response format
    article_responses = []
    for article in articles:
        article_dict = {
            "id": article.id,
            "url": article.url,
            "title": article.title,
            "summary": article.summary,
            "summary_bullets": article.summary_bullets,
            "tags": article.tags,
            "city_hints": article.city_hints,
            "company_tags": article.company_tags,
            "source_type": article.source_type,
            "platform": article.platform,
            "video_id": article.video_id,
            "thumbnail_url": article.thumbnail_url,
            "place_name": None,
            "published_at": article.published_at,
            "views": article.views,
            "saves": article.saves,
            "final_score": article.final_score
        }
        article_responses.append(ArticleResponse(**article_dict))
    
    return WealthFeedResponse(
        articles=article_responses,
        total=len(article_responses),
        updated_at=datetime.now().isoformat()
    )


@router.get("/gossip", response_model=GossipFeedResponse)
def get_gossip_feed(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get "八卦" (Gossip) feed - trending posts from 1point3acres, huaren.us, and Teamblind
    Improved blending: balances freshness, relevance, and engagement
    """
    import math
    
    # Show articles from teamblind.com, 1point3acres.com, and huaren.us
    # Prioritize articles with gossip_score if available
    from sqlalchemy import or_
    query = db.query(Article).filter(
        Article.source_type.in_(["di_li", "blind", "reddit", "gossip"]),
        or_(
            Article.final_score > 0,
            and_(Article.gossip_score.isnot(None), Article.gossip_score > 0)
        ),
        (
            Article.url.ilike('%teamblind.com%') |
            Article.url.ilike('%1point3acres.com%') |
            Article.url.ilike('%huaren.us%') |
            Article.url.ilike('%reddit.com%')
        )
    )
    
    # Fetch more articles than needed to calculate blended scores
    # Sort by gossip_score first if available, then by final_score
    from sqlalchemy import nullslast
    articles = query.order_by(
        nullslast(desc(Article.gossip_score)),
        desc(Article.fetched_at),
        desc(Article.final_score)
    ).limit(limit * 2).all()  # Fetch 2x to have more candidates for blending
    
    if not articles:
        return GossipFeedResponse(
            articles=[],
            total=0,
            filters={}
        )
    
    # Calculate blended scores in Python
    from datetime import timezone
    now = datetime.now(timezone.utc)  # Use timezone-aware datetime
    scored_articles = []
    
    for article in articles:
        # 1. Final score (relevance) - 40%
        relevance_score = article.final_score
        
        # 2. Freshness score - 30%
        # Articles from last 24h get full boost, decays over 7 days
        if article.fetched_at:
            # Ensure fetched_at is timezone-aware
            fetched_at = article.fetched_at
            if fetched_at.tzinfo is None:
                from pytz import UTC
                fetched_at = UTC.localize(fetched_at)
            age_seconds = (now - fetched_at).total_seconds()
            if age_seconds < 86400:  # < 24 hours
                freshness_score = 1.0
            elif age_seconds < 604800:  # < 7 days
                freshness_score = 1.0 - (age_seconds - 86400) / 518400
            else:  # Older than 7 days
                freshness_score = 0.3
        else:
            freshness_score = 0.3
        
        # 3. Engagement score - 20%
        # Normalize views + saves (log scale to prevent outliers)
        engagement_raw = article.views + article.saves * 2  # Saves weighted 2x
        engagement_score = math.log(max(engagement_raw, 1)) / 10.0  # Normalize to roughly 0-1
        engagement_score = min(engagement_score, 1.0)  # Cap at 1.0
        
        # 4. Source diversity - 10% (equal weight for both sources)
        diversity_score = 0.5
        
        # 5. Gossip score - boost if available (20% weight)
        gossip_boost = (article.gossip_score or 0) * 0.2
        
        # Calculate blended score (incorporate gossip_score)
        blended_score = (
            0.35 * relevance_score +
            0.25 * freshness_score +
            0.15 * engagement_score +
            0.10 * diversity_score +
            gossip_boost
        )
        
        scored_articles.append((blended_score, article))
    
    # Sort by blended score (descending), then by final_score as tiebreaker
    min_datetime = datetime.min.replace(tzinfo=timezone.utc)
    scored_articles.sort(key=lambda x: (x[0], x[1].final_score, x[1].fetched_at or min_datetime), reverse=True)
    
    # Take top N articles
    top_articles = [article for _, article in scored_articles[:limit]]
    
    return GossipFeedResponse(
        articles=[ArticleResponse.model_validate(a) for a in top_articles],
        total=len(top_articles),
        filters={}
    )

