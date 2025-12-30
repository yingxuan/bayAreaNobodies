"""
Tech API endpoints for trending tech news
"""
from fastapi import APIRouter, Query
from app.services.tech_trending_service import fetch_tech_trending
from app.services.ai_news_service import aggregate_ai_news, parse_time_ago
from typing import List, Dict
from datetime import datetime

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


@router.get("/ai-news")
def get_ai_news(
    limit: int = Query(default=6, ge=1, le=20, description="Number of items to return (target 4-6)")
):
    """
    Get aggregated AI news from multiple sources (Google CSE, Finnhub, Hacker News)
    Returns web-wide AI top news, not limited to Hacker News
    Ensures 4-6 items for homepage balance
    """
    # Target 5 items, minimum 4
    items = aggregate_ai_news(limit=min(limit, 6), target_min=4)
    
    # Format response to match frontend expectations
    formatted_items = []
    for item in items:
        formatted_items.append({
            "title": item["title"],
            "url": item["url"],
            "source": item["source"],
            "timeAgo": parse_time_ago(item.get("published_at")),
            "published_at": item.get("published_at").isoformat() if isinstance(item.get("published_at"), datetime) else None,
            "affectedTickers": [item["ticker"]] if item.get("ticker") else [],
            "category": None,
            "domain": item.get("domain", "")
        })
    
    return {
        "items": formatted_items,
        "total": len(formatted_items),
        "dataSource": "aggregated"
    }

