"""
Gossip API endpoints for 八卦 (Gossip) page
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc, case
from app.database import get_db
from app.models import Article
from app.schemas import ArticleResponse
from app.services.gossip_service import (
    check_gossip_budget_exceeded, get_gossip_usage_key
)
from typing import Optional
import os
import redis
from datetime import datetime, timezone

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None


@router.get("/feed")
def get_gossip_feed(
    source: Optional[str] = Query(None, description="Filter by source: 1point3acres, huaren, reddit"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get gossip feed with optional source filter
    Returns ranked gossip articles with gossip_score
    """
    # Query articles with gossip_score
    query = db.query(Article).filter(
        Article.gossip_score > 0,
        Article.source_type.in_(["di_li", "blind", "reddit", "gossip"]),
        (
            Article.url.ilike('%1point3acres.com%') |
            Article.url.ilike('%huaren.us%') |
            Article.url.ilike('%reddit.com%')
        )
    )
    
    if source:
        if source == "1point3acres":
            query = query.filter(Article.url.ilike('%1point3acres.com%'))
        elif source == "huaren":
            query = query.filter(Article.url.ilike('%huaren.us%'))
        elif source == "reddit":
            query = query.filter(Article.url.ilike('%reddit.com%'))
    
    # Sort by gossip_score (descending), then freshness
    articles = query.order_by(
        desc(Article.gossip_score),
        desc(Article.fetched_at)
    ).limit(limit).all()
    
    # Check data freshness
    quota_exceeded = check_gossip_budget_exceeded()
    data_freshness = "stale_due_to_quota" if quota_exceeded else "fresh"
    
    # Get usage info if available
    usage_info = None
    if redis_client:
        usage_key = get_gossip_usage_key()
        current_usage = redis_client.get(usage_key)
        if current_usage:
            try:
                usage_info = {
                    "current_usage": int(current_usage),
                    "daily_budget": int(os.getenv("GOSSIP_CSE_DAILY_BUDGET", "50"))
                }
            except:
                pass
    
    return {
        "articles": [ArticleResponse.model_validate(a) for a in articles],
        "total": len(articles),
        "data_freshness": data_freshness,
        "usage_info": usage_info,
        "filters": {"source": source} if source else {}
    }

