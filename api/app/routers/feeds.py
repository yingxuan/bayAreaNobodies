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
    DealsFeedResponse, WealthFeedResponse, GossipFeedResponse,
    StockData, StockNewsItem
)
from app.services.stock_service import (
    get_stock_price, get_stock_news, get_stock_daily_trend, get_financial_advice
)
from typing import Optional, List, Dict
from datetime import datetime
import json

router = APIRouter()

# Tracked stocks for "暴富" feed
TRACKED_STOCKS = ["GOOG", "NVDA", "MSFT", "VOO", "TSLA", "VRT", "VST", "TQQQ", "SOXL", "OKLO", "NAIL", "NBIS", "CRWV"]


@router.get("/food", response_model=FoodRadarFeedResponse)
def get_food_feed(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get "美食" (Food) feed - local Chinese food in Bay Area
    ONLY shows food_radar source_type articles, excludes all blind/di_li content
    """
    # Only show food_radar articles - no blind or di_li content
    # Allow articles with final_score >= 0 (including 0) to show all food_radar content
    query = db.query(Article).filter(
        Article.source_type == "food_radar"  # ONLY food_radar articles
    )
    
    # Sort by hybrid of freshness (fetched_at) and relevance (final_score)
    # Prioritize articles with video_id/thumbnail_url for better media display
    # Use fetched_at for freshness, final_score for relevance
    from sqlalchemy import case
    articles = query.order_by(
        desc(case((Article.video_id.isnot(None), 1), else_=0)),  # Articles with video_id first
        desc(case((Article.thumbnail_url.isnot(None), 1), else_=0)),  # Then articles with thumbnail
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
    Get "羊毛" (Deals) feed - all food coupons and discounts in Bay Area
    Blends all coupons, ranked by confidence and freshness
    """
    # Get all coupons, focus on food-related but include all
    # Filter out invalid coupons (only from dealmoon/dealnews)
    query = db.query(Coupon).filter(
        (Coupon.source_url.ilike('%dealmoon.com%')) | 
        (Coupon.source_url.ilike('%dealnews.com%'))
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
def get_wealth_feed():
    """
    Get "暴富" (Wealth) feed - real-time stock prices, daily trends, news, and financial analysis
    Uses Yahoo Finance for prices/trends and Gemini AI for financial advice
    """
    stocks_data = []
    
    for ticker in TRACKED_STOCKS:
        try:
            # Get current price
            current_price = get_stock_price(ticker)
            
            # Get daily trend (change amount and percent)
            change_amount, change_percent = get_stock_daily_trend(ticker)
            if change_percent is None:
                change_percent = 0.0
            if change_amount is None:
                change_amount = 0.0
            
            # Get recent news (last 24 hours)
            news_items = get_stock_news(ticker, range_hours=24)
            
            # Get financial advice from Gemini
            financial_advice = get_financial_advice(
                ticker=ticker,
                current_price=current_price,
                change_percent=change_percent,
                news_items=news_items
            )
            
            stocks_data.append(StockData(
                ticker=ticker,
                current_price=current_price,
                change_percent=change_percent,
                change_amount=change_amount,
                news=[StockNewsItem.model_validate(item) for item in news_items[:5]],
                news_count=len(news_items),
                financial_advice=financial_advice
            ))
        except Exception as e:
            stocks_data.append(StockData(
                ticker=ticker,
                current_price=None,
                change_percent=0.0,
                change_amount=0.0,
                news=[],
                news_count=0,
                financial_advice=None,
                error=str(e)
            ))
    
    return WealthFeedResponse(
        stocks=stocks_data,
        total=len(stocks_data),
        updated_at=datetime.now().isoformat()
    )


@router.get("/gossip", response_model=GossipFeedResponse)
def get_gossip_feed(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get "八卦" (Gossip) feed - trending posts from 1point3acres and Teamblind
    Improved blending: balances freshness, relevance, and engagement
    """
    import math
    
    # Get all articles from di_li and blind (fetch more to calculate blended scores)
    query = db.query(Article).filter(
        Article.source_type.in_(["di_li", "blind"]),
        Article.final_score > 0
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

