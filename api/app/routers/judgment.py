"""
Judgment API endpoints
Returns opinionated judgments for homepage sections
"""
from fastapi import APIRouter, Query, HTTPException, Depends
from app.services.judgment_service import (
    generate_portfolio_judgment,
    generate_mortgage_judgment,
    generate_offer_market_judgment,
    generate_food_place_tag,
    generate_entertainment_description
)
from typing import List, Dict, Optional
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/portfolio")
def get_portfolio_judgment(
    day_gain: float = Query(..., description="Today's gain/loss in dollars"),
    day_gain_percent: float = Query(..., description="Today's gain/loss percentage"),
    index_change: Optional[float] = Query(None, description="SPY index change percentage"),
    top_movers: Optional[str] = Query(None, description="JSON string of top movers: [{\"ticker\": \"NVDA\", \"day_gain_percent\": 2.5}]")
) -> Dict:
    """
    Get portfolio judgment
    Question: "我今天的钱整体状态如何？"
    
    Returns judgment sentence (<= 25 Chinese characters)
    """
    # Parse top movers
    movers_list = []
    if top_movers:
        try:
            import json
            movers_list = json.loads(top_movers)
        except:
            pass
    
    judgment = generate_portfolio_judgment(
        day_gain=day_gain,
        day_gain_percent=day_gain_percent,
        top_movers=movers_list,
        index_change=index_change
    )
    
    return {
        "judgment": judgment,
        "question": "我今天的钱整体状态如何？"
    }


@router.get("/mortgage")
def get_mortgage_judgment(
    rate_30y: float = Query(..., description="30-year fixed mortgage rate"),
    rate_7_1_arm: float = Query(..., description="7/1 ARM rate"),
    rate_trend: Optional[str] = Query(None, description="Comma-separated list of recent rates for trend analysis")
) -> Dict:
    """
    Get mortgage rate judgment
    Question: "我现在该不该关心买房或 refi？"
    
    Returns judgment sentence (<= 25 Chinese characters)
    """
    # Parse rate trend
    trend_list = None
    if rate_trend:
        try:
            trend_list = [float(r.strip()) for r in rate_trend.split(",")]
        except:
            pass
    
    judgment = generate_mortgage_judgment(
        rate_30y=rate_30y,
        rate_7_1_arm=rate_7_1_arm,
        rate_trend=trend_list
    )
    
    return {
        "judgment": judgment,
        "question": "我现在该不该关心买房或 refi？"
    }


@router.get("/offer-market")
def get_offer_market_judgment(
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get offer market temperature and risk note
    Question: "市场现在给码农什么价？"
    
    Returns: {
        "temperature": "冷" | "正常" | "热",
        "risk_note": "<= 25 Chinese characters"
    }
    """
    from app.models import Article
    from datetime import datetime, timedelta
    import pytz
    
    # Get recent offers
    cutoff_time = datetime.now(pytz.UTC) - timedelta(days=3)
    offer_articles = db.query(Article).filter(
        Article.url.ilike('%1point3acres.com%'),
        Article.fetched_at >= cutoff_time
    ).all()
    
    offer_keywords = ['包裹', 'offer', 'tc', 'total comp', '年包', 'package']
    recent_offers = []
    for article in offer_articles:
        text = f"{article.title or ''} {article.summary or ''}".lower()
        if any(kw in text for kw in offer_keywords):
            recent_offers.append({
                "title": article.title,
                "url": article.url
            })
    
    # Count layoff/hiring news
    layoff_keywords = ['layoff', '裁员', 'firing', 'termination']
    hiring_keywords = ['hiring', '招聘', 'recruiting', 'open position']
    
    layoff_count = 0
    hiring_count = 0
    
    for article in offer_articles[:50]:  # Check recent articles
        text = f"{article.title or ''} {article.summary or ''}".lower()
        if any(kw in text for kw in layoff_keywords):
            layoff_count += 1
        if any(kw in text for kw in hiring_keywords):
            hiring_count += 1
    
    result = generate_offer_market_judgment(
        recent_offers=recent_offers[:10],
        layoff_news_count=layoff_count,
        hiring_news_count=hiring_count
    )
    
    return {
        **result,
        "question": "市场现在给码农什么价？"
    }


@router.get("/food-tag")
def get_food_tag(
    place_name: str = Query(..., description="Place name"),
    cuisine_type: str = Query(..., description="Cuisine type: chinese or boba"),
    rating: Optional[float] = Query(None, description="Rating (optional)")
) -> Dict:
    """
    Get short tag for food/boba place (OPTIONAL)
    Returns: <= 4 Chinese characters
    """
    tag = generate_food_place_tag(
        place_name=place_name,
        cuisine_type=cuisine_type,
        rating=rating
    )
    
    return {
        "tag": tag,
        "place_name": place_name
    }


@router.get("/entertainment-description")
def get_entertainment_description(
    title: str = Query(..., description="Content title"),
    source: str = Query("", description="Source (optional)")
) -> Dict:
    """
    Get short description for entertainment content (OPTIONAL)
    Returns: <= 30 Chinese characters
    """
    description = generate_entertainment_description(
        title=title,
        source=source
    )
    
    return {
        "description": description,
        "title": title
    }
