"""
Unified feed endpoints for the 4 main feeds:
1. 美食 (Food) - food content from YouTube, Instagram, TikTok
2. 羊毛 (Deals) - food coupons and discounts
3. 暴富 (Wealth) - stock prices and news
4. 八卦 (Gossip) - trending posts from 1point3acres and Teamblind
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.database import get_db
from app.models import Article, Coupon
from app.schemas import (
    ArticleResponse, CouponResponse, FoodRadarFeedResponse,
    DealsFeedResponse, WealthFeedResponse, GossipFeedResponse
)
from typing import Optional, List, Dict
from datetime import datetime
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
    Blends all coupons, ranked by confidence and freshness
    """
    # Show coupons from dealmoon.com, 1point3acres.com, and huaren.us
    query = db.query(Coupon).filter(
        (
            Coupon.source_url.ilike('%dealmoon.com%') |
            Coupon.source_url.ilike('%1point3acres.com%') |
            Coupon.source_url.ilike('%huaren.us%')
        )
    )
    
    # Sort by confidence (relevance) and recency (freshness)
    coupons = query.order_by(
        desc(Coupon.confidence),
        desc(Coupon.created_at)
    ).limit(limit).all()
    
    return DealsFeedResponse(
        coupons=[CouponResponse.model_validate(c) for c in coupons],
        total=len(coupons),
        filters={}
    )


@router.get("/wealth", response_model=WealthFeedResponse)
def get_wealth_feed(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get "暴富" (Wealth) feed - latest YouTube videos from US stock investment bloggers
    Shows videos from the last 24 hours only
    """
    from datetime import timedelta
    import pytz
    
    # Only show wealth articles from youtube.com, published in the last 24 hours
    cutoff_time = datetime.now(pytz.UTC) - timedelta(days=1)
    
    query = db.query(Article).filter(
        Article.source_type == "wealth",
        Article.url.ilike('%youtube.com%'),
        Article.published_at >= cutoff_time  # Only last 24 hours
    )
    
    # Sort by freshness (published_at) and relevance (final_score)
    from sqlalchemy import case
    articles = query.order_by(
        desc(Article.published_at),  # Most recent first
        desc(case((Article.video_id.isnot(None), 1), else_=0)),  # Videos first
        desc(Article.final_score)
    ).limit(limit).all()
    
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
    query = db.query(Article).filter(
        Article.source_type.in_(["di_li", "blind"]),
        Article.final_score > 0,
        (
            Article.url.ilike('%teamblind.com%') |
            Article.url.ilike('%1point3acres.com%') |
            Article.url.ilike('%huaren.us%')
        )
    )
    
    # Fetch more articles than needed to calculate blended scores
    articles = query.order_by(
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
    now = datetime.now()
    scored_articles = []
    
    for article in articles:
        # 1. Final score (relevance) - 40%
        relevance_score = article.final_score
        
        # 2. Freshness score - 30%
        # Articles from last 24h get full boost, decays over 7 days
        if article.fetched_at:
            age_seconds = (now - article.fetched_at).total_seconds()
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
        
        # Calculate blended score
        blended_score = (
            0.40 * relevance_score +
            0.30 * freshness_score +
            0.20 * engagement_score +
            0.10 * diversity_score
        )
        
        scored_articles.append((blended_score, article))
    
    # Sort by blended score (descending), then by final_score as tiebreaker
    scored_articles.sort(key=lambda x: (x[0], x[1].final_score, x[1].fetched_at or datetime.min), reverse=True)
    
    # Take top N articles
    top_articles = [article for _, article in scored_articles[:limit]]
    
    return GossipFeedResponse(
        articles=[ArticleResponse.model_validate(a) for a in top_articles],
        total=len(top_articles),
        filters={}
    )

