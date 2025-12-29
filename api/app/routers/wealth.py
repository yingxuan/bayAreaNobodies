"""
Wealth API endpoints for 暴富 (Wealth) page
Additional endpoints for offer posts and lottery info
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.database import get_db
from app.models import Article
from app.schemas import ArticleResponse
from typing import List
from datetime import datetime, timedelta
import pytz
import re

router = APIRouter()


@router.get("/offers")
def get_high_offers(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get 1point3acres posts about 包裹 (package/offer) from last 3 days
    Focuses on hottest posts (by views, saves, final_score)
    """
    # Only show posts from last 3 days
    cutoff_time = datetime.now(pytz.UTC) - timedelta(days=3)
    
    # Query articles from 1point3acres.com, last 3 days
    query = db.query(Article).filter(
        Article.url.ilike('%1point3acres.com%'),
        Article.source_type.in_(["di_li", "gossip"]),
        Article.fetched_at >= cutoff_time  # Last 3 days
    )
    
    articles = query.all()
    
    # Filter to only posts that mention 包裹/offer/TC/total comp
    offer_keywords = ['包裹', 'offer', 'tc', 'total comp', 'total compensation', '年包', 'package', 'compensation']
    filtered_articles = []
    
    for article in articles:
        title = (article.title or "").lower()
        summary = (article.summary or "").lower()
        text = f"{title} {summary}"
        
        # Must contain at least one offer-related keyword
        if any(keyword.lower() in text for keyword in offer_keywords):
            filtered_articles.append(article)
    
    # Sort by "热度" (hotness): views + saves + final_score
    # Calculate hotness score: views + saves*2 + final_score*100
    def calculate_hotness(article):
        views = article.views or 0
        saves = article.saves or 0
        score = article.final_score or 0
        # Weight: saves worth 2x views, final_score worth 100x views
        return views + saves * 2 + score * 100
    
    filtered_articles.sort(
        key=lambda a: (
            -calculate_hotness(a),  # Hotness first (descending)
            -(a.fetched_at.timestamp() if a.fetched_at else 0)  # Then freshness
        )
    )
    
    articles = filtered_articles[:limit]
    
    return {
        "articles": [ArticleResponse.model_validate(a) for a in articles],
        "total": len(articles)
    }


@router.get("/metals")
def get_metals_prices():
    """
    Get real-time gold and silver prices
    Returns current prices for GC=F (Gold) and SI=F (Silver)
    """
    from app.services.metals_service import fetch_metals_prices
    return fetch_metals_prices()


@router.get("/powerball")
def get_powerball_info():
    """
    Get Powerball information
    Returns current jackpot amount and next drawing time
    """
    from app.services.powerball_service import fetch_powerball_info
    return fetch_powerball_info()


@router.get("/btc")
def get_btc_price():
    """
    Get Bitcoin (BTC) price
    Returns current BTC price in USD
    """
    from app.services.crypto_service import fetch_btc_price
    return fetch_btc_price()


@router.get("/jumbo-loan")
def get_jumbo_loan_rate():
    """
    Get California Jumbo Loan 7-year ARM rate
    Returns current rate percentage
    """
    from app.services.loan_service import fetch_jumbo_7arm_rate
    return fetch_jumbo_7arm_rate()


@router.get("/tbill")
def get_tbill_rate():
    """
    Get T-bill (Treasury Bill) short-term rate
    Returns current rate percentage
    """
    from app.services.treasury_service import fetch_tbill_rate
    return fetch_tbill_rate()

