import httpx
import os
import redis
import json
from typing import List, Optional
from datetime import datetime, timedelta
from app.schemas import StockNewsItem

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None


def get_stock_price(ticker: str) -> float:
    """
    Get current stock price (mock implementation for MVP)
    In production, use Finnhub or Polygon API
    """
    # Mock prices for common stocks
    mock_prices = {
        "NVDA": 450.0,
        "AAPL": 180.0,
        "GOOGL": 140.0,
        "MSFT": 380.0,
        "AMZN": 150.0,
        "META": 320.0,
        "TSLA": 250.0,
    }
    
    if ticker.upper() in mock_prices:
        return mock_prices[ticker.upper()]
    
    # If Finnhub key is available, try real API
    if FINNHUB_API_KEY:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker.upper()}&token={FINNHUB_API_KEY}"
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("c"):  # current price
                        return float(data["c"])
        except Exception as e:
            print(f"Error fetching stock price for {ticker}: {e}")
    
    # Default mock price
    return 100.0


def get_stock_news(ticker: str, range_hours: int = 24) -> List[StockNewsItem]:
    """
    Get stock news from Finnhub or return mock data
    
    Args:
        ticker: Stock ticker symbol
        range_hours: Time range in hours
    
    Returns:
        List of StockNewsItem
    """
    cache_key = f"stock_news:{ticker}:{range_hours}"
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            return [StockNewsItem(**item) for item in data]
    
    news_items = []
    
    if FINNHUB_API_KEY:
        try:
            url = f"https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": ticker.upper(),
                "from": (datetime.now() - timedelta(hours=range_hours)).strftime("%Y-%m-%d"),
                "to": datetime.now().strftime("%Y-%m-%d"),
                "token": FINNHUB_API_KEY
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    for item in data[:10]:  # Limit to 10 items
                        try:
                            published_at = None
                            if item.get("datetime"):
                                published_at = datetime.fromtimestamp(item["datetime"])
                            
                            news_items.append(StockNewsItem(
                                headline=item.get("headline", ""),
                                summary=item.get("summary", ""),
                                url=item.get("url", ""),
                                published_at=published_at,
                                source=item.get("source", "")
                            ))
                        except Exception:
                            continue
        except Exception as e:
            print(f"Error fetching stock news from Finnhub: {e}")
    
    # Return mock data if no real data
    if not news_items:
        news_items = [
            StockNewsItem(
                headline=f"{ticker} shows strong performance",
                summary=f"Mock news summary for {ticker}",
                url=f"https://example.com/news/{ticker.lower()}",
                published_at=datetime.now() - timedelta(hours=i),
                source="Mock News"
            )
            for i in range(3)
        ]
    
    # Cache for 15 minutes
    if redis_client:
        redis_client.setex(
            cache_key,
            900,
            json.dumps([item.dict() for item in news_items])
        )
    
    return news_items

