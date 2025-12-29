"""
Deals API endpoints for 羊毛 (Deals) page
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Coupon
from app.schemas import CouponResponse
from app.services.deals_service import (
    DEAL_SOURCES, search_and_store_deals,
    check_deals_budget_exceeded, get_deals_usage_key
)
from typing import Optional, List
import os
import redis
from datetime import datetime

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None
DEALS_RUN_ADMIN_TOKEN = os.getenv("DEALS_RUN_ADMIN_TOKEN", "")


@router.get("/sources")
def get_sources():
    """Get list of curated deal sources"""
    return {"sources": DEAL_SOURCES}


@router.get("/feed")
def get_deals_feed(
    category: Optional[str] = Query(None, description="Filter by category: bank, card, brokerage, life"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get deals feed with optional category filter
    Returns ranked deals with data freshness indicator
    """
    # Only show deals from 1point3acres.com, huaren.us, and dealmoon.com (exclude YouTube)
    query = db.query(Coupon).filter(
        Coupon.score > 0,  # Only show scored deals
        Coupon.canonical_url.isnot(None),  # Only show properly processed deals
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
    
    if category:
        query = query.filter(Coupon.category == category)
    
    # Sort by category priority (food_fast and retail_family first), then score and freshness
    from sqlalchemy import case
    
    category_priority = case(
        (Coupon.category == 'food_fast', 3),
        (Coupon.category == 'retail_family', 2),
        else_=1
    )
    
    deals = query.order_by(
        desc(category_priority),  # Priority categories first
        desc(Coupon.score),
        desc(Coupon.fetched_at)
    ).limit(limit).all()
    
    # Check data freshness
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
    
    return {
        "coupons": [CouponResponse.model_validate(c) for c in deals],
        "total": len(deals),
        "data_freshness": data_freshness,
        "usage_info": usage_info,
        "filters": {"category": category} if category else {}
    }


@router.post("/run")
def run_deals_search(
    category: Optional[str] = Query(None, description="Optional category filter: bank, card, brokerage, life"),
    admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    db: Session = Depends(get_db)
):
    """
    Manually trigger deals search (admin/dev only)
    Requires DEALS_RUN_ADMIN_TOKEN in header or env
    """
    # Check admin token
    if DEALS_RUN_ADMIN_TOKEN:
        if not admin_token or admin_token != DEALS_RUN_ADMIN_TOKEN:
            raise HTTPException(status_code=403, detail="Invalid admin token")
    # If no token set, allow (for dev)
    
    try:
        processed, skipped, quota_exceeded = search_and_store_deals(db, category_filter=category)
        
        return {
            "status": "success",
            "processed": processed,
            "skipped": skipped,
            "quota_exceeded": quota_exceeded,
            "category": category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running deals search: {str(e)}")

