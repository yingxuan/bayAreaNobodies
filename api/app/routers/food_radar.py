from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Article
from app.schemas import ArticleResponse
from app.services.google_search import check_budget_exceeded
from typing import Optional, List, Dict, Any
import json

router = APIRouter()


@router.get("/feed")
def get_food_radar_feed(
    city: Optional[str] = Query(None, description="Filter by city"),
    platform: Optional[str] = Query(None, description="Filter by platform: youtube, tiktok, instagram, web"),
    category: Optional[str] = Query(None, description="Filter by category (food tag)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get Food Radar feed - food exploration content from YouTube, TikTok, Instagram, and web
    Sorted by newest first, then by relevance score
    """
    # Query only food_radar source_type articles
    # Allow articles with final_score >= 0 (including 0) to show all food_radar content
    query = db.query(Article).filter(
        Article.source_type == "food_radar"
    )
    
    # Filter by city if provided
    if city:
        query = query.filter(Article.city_hints.ilike(f"%{city}%"))
    
    # Filter by platform if provided
    if platform:
        query = query.filter(Article.platform == platform.lower())
    
    # Filter by category (food tag) if provided
    if category:
        # Tags are stored as JSON array, so we search within the JSON string
        query = query.filter(Article.tags.ilike(f"%{category}%"))
    
    # Sort by newest first (fetched_at), then by relevance score
    articles = query.order_by(
        desc(Article.fetched_at),
        desc(Article.final_score)
    ).limit(limit).all()
    
    # Convert to response format
    article_responses = []
    for article in articles:
        # Parse tags to extract place name if present
        tags_list = []
        place_name = None
        if article.tags:
            try:
                tags_list = json.loads(article.tags)
                # Look for place: prefix in tags
                for tag in tags_list:
                    if isinstance(tag, str) and tag.startswith("place:"):
                        place_name = tag.replace("place:", "").strip()
                        tags_list = [t for t in tags_list if not (isinstance(t, str) and t.startswith("place:"))]
                        break
            except:
                pass
        
        # Create ArticleResponse (place_name is already in schema)
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
    
    # Check if data is fresh or stale due to quota
    data_freshness = "stale_due_to_quota" if check_budget_exceeded() else "fresh"
    
    return {
        "articles": article_responses,
        "total": len(article_responses),
        "data_freshness": data_freshness,
        "filters": {
            "city": city,
            "platform": platform,
            "category": category
        }
    }

