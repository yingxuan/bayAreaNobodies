"""
Metals service - fetch real-time gold and silver prices
Uses Google CSE to search Google Finance for gold and silver prices
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


def get_metals_cache_key() -> str:
    """Get Redis key for metals cache"""
    return "metals:prices"


def fetch_metals_prices() -> Dict:
    """
    Fetch real-time gold and silver prices
    Returns current prices for GC=F (Gold) and SI=F (Silver)
    """
    # Check cache first (cache for 2 minutes)
    if redis_client:
        cached = redis_client.get(get_metals_cache_key())
        if cached:
            import json
            try:
                return json.loads(cached)
            except:
                pass
    
    result = {
        "gold": {"price": 0.0, "change": 0.0, "change_percent": 0.0},
        "silver": {"price": 0.0, "change": 0.0, "change_percent": 0.0},
        "data_freshness": "no_data",
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    # Check budget before making API calls
    if check_budget_exceeded():
        # Return placeholder if budget exceeded
        result["gold"] = {"price": 2650.0, "change": 0.0, "change_percent": 0.0}
        result["silver"] = {"price": 30.5, "change": 0.0, "change_percent": 0.0}
        result["data_freshness"] = "placeholder"
        result["note"] = "数据暂不可用，显示示例数据。"
        return result
    
    try:
        # Search Google Finance for gold price
        gold_query = "site:google.com/finance gold price XAUUSD"
        gold_results = search_google(gold_query, num=5, date_restrict="d1")
        
        if gold_results.get("items"):
            for item in gold_results.get("items", [])[:3]:
                text = f"{item.get('title', '')} {item.get('snippet', '')}"
                # Look for price patterns: $2,650.00, 2650.00, etc.
                price_patterns = [
                    r'\$?\s*(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|per ounce|oz|/oz)?',
                    r'(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s*(?:usd|per ounce)',
                ]
                for pattern in price_patterns:
                    price_match = re.search(pattern, text, re.IGNORECASE)
                    if price_match:
                        price_str = price_match.group(1).replace(',', '')
                        try:
                            price = float(price_str)
                            if 1000 < price < 5000:  # Reasonable gold price range
                                result["gold"]["price"] = round(price, 2)
                                print(f"Gold price from Google Finance: ${price:.2f}")
                                break
                        except:
                            pass
                if result["gold"]["price"] > 0:
                    break
        
        # Search Google Finance for silver price
        silver_query = "site:google.com/finance silver price XAGUSD"
        silver_results = search_google(silver_query, num=5, date_restrict="d1")
        
        if silver_results.get("items"):
            for item in silver_results.get("items", [])[:3]:
                text = f"{item.get('title', '')} {item.get('snippet', '')}"
                # Look for price patterns: $30.50, 30.5, etc.
                price_patterns = [
                    r'\$?\s*(\d{1,2}(?:\.\d{2})?)\s*(?:usd|per ounce|oz|/oz)?',
                    r'(\d{1,2}(?:\.\d{2})?)\s*(?:usd|per ounce)',
                ]
                for pattern in price_patterns:
                    price_match = re.search(pattern, text, re.IGNORECASE)
                    if price_match:
                        price_str = price_match.group(1)
                        try:
                            price = float(price_str)
                            if 20 < price < 50:  # Reasonable silver price range
                                result["silver"]["price"] = round(price, 2)
                                print(f"Silver price from Google Finance: ${price:.2f}")
                                break
                        except:
                            pass
                if result["silver"]["price"] > 0:
                    break
        
        # Only mark as fresh if we got both prices
        if result["gold"]["price"] > 0 and result["silver"]["price"] > 0:
            result["data_freshness"] = "fresh"
        elif result["gold"]["price"] > 0 or result["silver"]["price"] > 0:
            result["data_freshness"] = "partial"
        else:
            # Set reasonable placeholder values
            result["gold"] = {"price": 2650.0, "change": 0.0, "change_percent": 0.0}
            result["silver"] = {"price": 30.5, "change": 0.0, "change_percent": 0.0}
            result["data_freshness"] = "placeholder"
            result["note"] = "数据暂不可用，显示示例数据。"
        
    except Exception as e:
        print(f"Error fetching metals prices: {e}")
        import traceback
        traceback.print_exc()
        # Set placeholder values on error
        result["gold"] = {"price": 2650.0, "change": 0.0, "change_percent": 0.0}
        result["silver"] = {"price": 30.5, "change": 0.0, "change_percent": 0.0}
        result["data_freshness"] = "placeholder"
        result["note"] = "数据暂不可用，显示示例数据。"
    
    # Cache for 2 minutes
    if redis_client:
        import json
        redis_client.setex(get_metals_cache_key(), 120, json.dumps(result))
    
    return result

