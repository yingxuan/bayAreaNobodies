"""
Crypto service - fetch real-time Bitcoin (BTC) price
Uses Google CSE to search Google Finance for BTC price
"""
import os
import redis
import re
from typing import Dict, Optional
from datetime import datetime
import pytz
from app.services.google_search import search_google, check_budget_exceeded

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None


def get_btc_cache_key() -> str:
    """Get Redis key for BTC cache"""
    return "crypto:btc:price"


def fetch_btc_price() -> Dict:
    """
    Fetch Bitcoin price using Google CSE to search Google Finance
    Returns current BTC price in USD
    """
    # Check cache first (cache for 2 minutes)
    if redis_client:
        cached = redis_client.get(get_btc_cache_key())
        if cached:
            import json
            try:
                return json.loads(cached)
            except:
                pass
    
    result = {
        "price": 0.0,
        "change": 0.0,
        "change_percent": 0.0,
        "data_freshness": "no_data",
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    # Check budget before making API calls
    if check_budget_exceeded():
        # Return placeholder if budget exceeded
        result = {
            "price": 95000.0,
            "change": 0.0,
            "change_percent": 0.0,
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。"
        }
        return result
    
    try:
        # Search Google Finance for BTC price
        btc_query = "site:google.com/finance bitcoin BTC price"
        btc_results = search_google(btc_query, num=5, date_restrict="d1")
        
        if btc_results.get("items"):
            for item in btc_results.get("items", [])[:3]:
                text = f"{item.get('title', '')} {item.get('snippet', '')}"
                # Look for price patterns: $95,000, $95,000.00, etc.
                price_patterns = [
                    r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|usdt)?',
                    r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|usdt)',
                ]
                for pattern in price_patterns:
                    price_match = re.search(pattern, text, re.IGNORECASE)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        try:
                            price = float(price_str)
                            if 10000 < price < 200000:  # Reasonable BTC price range
                                result["price"] = round(price, 2)
                                result["data_freshness"] = "fresh"
                                print(f"BTC price from Google Finance: ${price:.2f}")
                                break
                        except:
                            pass
                if result["price"] > 0:
                    break
        
        # If no data found, use placeholder
        if result["price"] == 0.0:
            result = {
                "price": 95000.0,
                "change": 0.0,
                "change_percent": 0.0,
                "data_freshness": "placeholder",
                "updated_at": datetime.now(pytz.UTC).isoformat(),
                "note": "数据暂不可用，显示示例数据。"
            }
        
    except Exception as e:
        print(f"Error fetching BTC price: {e}")
        import traceback
        traceback.print_exc()
        # Set placeholder on error
        result = {
            "price": 95000.0,
            "change": 0.0,
            "change_percent": 0.0,
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。"
        }
    
    # Cache for 2 minutes
    if redis_client:
        import json
        redis_client.setex(get_btc_cache_key(), 120, json.dumps(result))
    
    return result

