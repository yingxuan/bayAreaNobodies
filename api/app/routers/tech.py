"""
Tech API endpoints for trending tech news
"""
from fastapi import APIRouter, Query
from app.services.tech_trending_service import fetch_tech_trending

router = APIRouter()


@router.get("/trending")
def get_tech_trending(
    source: str = Query(default="hn", description="Source: hn (Hacker News)"),
    limit: int = Query(default=3, ge=1, le=50, description="Number of items to return")
):
    """
    Get trending tech news from specified source
    
    Currently supports:
    - hn: Hacker News (via Algolia API)
    
    Returns cached data with 10-minute TTL.
    Falls back to mock data if API fails.
    Items are sorted by score (descending) for stable ordering.
    """
    return fetch_tech_trending(source=source, limit=limit)

