"""
Treasury service - fetch real-time T-bill (Treasury Bill) short-term rates
Uses Google CSE to search for current T-bill rates
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


def get_tbill_cache_key() -> str:
    """Get Redis key for T-bill rates cache"""
    return "treasury:tbill:rate"


def fetch_tbill_rate() -> Dict:
    """
    Fetch T-bill (Treasury Bill) short-term rate using Google CSE
    Returns current rate percentage (typically 3-month or 6-month T-bill)
    """
    # Check cache first (cache for 2 hours)
    if redis_client:
        cached = redis_client.get(get_tbill_cache_key())
        if cached:
            import json
            try:
                return json.loads(cached)
            except:
                pass
    
    result = {
        "rate": 0.0,
        "maturity": "3-month",  # Default to 3-month
        "data_freshness": "no_data",
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    # Check budget before making API calls
    if check_budget_exceeded():
        # Return placeholder if budget exceeded
        result = {
            "rate": 5.2,
            "maturity": "3-month",
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。"
        }
        return result
    
    try:
        # Search for T-bill rates
        queries = [
            "T-bill treasury bill rate today",
            "3 month treasury bill rate current",
            "T-bill yield today",
        ]
        
        for query in queries[:1]:  # Limit to 1 query to save quota
            try:
                results = search_google(query, num=10, date_restrict="d1")
                if results.get("error"):
                    print(f"Google CSE error: {results.get('error')}")
                    continue
                
                items = results.get("items", [])
                if not items:
                    print(f"No results for query: {query}")
                    continue
                
                print(f"Found {len(items)} results for T-bill search")
                
                for item in items:
                    snippet = item.get("snippet", "")
                    title = item.get("title", "")
                    text = f"{title} {snippet}".lower()
                    
                    # Extract rate percentage
                    if "t-bill" in text or "treasury bill" in text or "tbill" in text:
                        # Look for percentage patterns: 5.2%, 5.20%, etc.
                        rate_patterns = [
                            r'(\d{1,2}\.?\d{0,2})\s*%',  # 5.2% or 5.20%
                            r'yield[:\s]+(\d{1,2}\.?\d{0,2})',  # yield: 5.2
                            r'rate[:\s]+(\d{1,2}\.?\d{0,2})',  # rate: 5.2
                            r'(\d{1,2}\.?\d{0,2})\s*percent',  # 5.2 percent
                        ]
                        
                        for pattern in rate_patterns:
                            rate_match = re.search(pattern, text, re.IGNORECASE)
                            if rate_match:
                                rate_str = rate_match.group(1)
                                try:
                                    rate = float(rate_str)
                                    if 0.5 <= rate <= 10.0:  # Reasonable T-bill rate range
                                        result["rate"] = round(rate, 2)
                                        result["data_freshness"] = "fresh"
                                        
                                        # Try to detect maturity
                                        if "3 month" in text or "3-month" in text:
                                            result["maturity"] = "3-month"
                                        elif "6 month" in text or "6-month" in text:
                                            result["maturity"] = "6-month"
                                        
                                        print(f"Found T-bill rate: {rate}% ({result['maturity']})")
                                        break
                                except:
                                    pass
                        if result["rate"] > 0:
                            break
            except Exception as e:
                print(f"Error fetching T-bill rate for query '{query}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # If no data found, use placeholder
        if result["rate"] == 0.0:
            result = {
                "rate": 5.2,
                "maturity": "3-month",
                "data_freshness": "placeholder",
                "updated_at": datetime.now(pytz.UTC).isoformat(),
                "note": "数据暂不可用，显示示例数据。"
            }
        
    except Exception as e:
        print(f"Error fetching T-bill rate: {e}")
        import traceback
        traceback.print_exc()
        # Set placeholder on error
        result = {
            "rate": 5.2,
            "maturity": "3-month",
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。"
        }
    
    # Cache for 2 hours
    if redis_client:
        import json
        redis_client.setex(get_tbill_cache_key(), 7200, json.dumps(result))
    
    return result

