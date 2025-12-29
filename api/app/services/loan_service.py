"""
Loan service - fetch real-time California Jumbo Loan 7-year ARM rates
Uses Google CSE to search for current mortgage rates
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


def get_loan_cache_key() -> str:
    """Get Redis key for loan rates cache"""
    return "loan:jumbo_7arm:rate"


def fetch_jumbo_7arm_rate() -> Dict:
    """
    Fetch California Jumbo Loan 7-year ARM rate using Google CSE
    Returns current rate percentage
    """
    # Check cache first (cache for 4 hours)
    if redis_client:
        cached = redis_client.get(get_loan_cache_key())
        if cached:
            import json
            try:
                return json.loads(cached)
            except:
                pass
    
    result = {
        "rate": 0.0,
        "data_freshness": "no_data",
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    # Check budget before making API calls
    if check_budget_exceeded():
        # Return placeholder if budget exceeded
        result = {
            "rate": 6.5,
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。"
        }
        return result
    
    try:
        # Search for California Jumbo Loan 7-year ARM rates
        queries = [
            "California jumbo loan 7 year ARM rate today",
            "CA jumbo mortgage 7/1 ARM current rate",
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
                
                print(f"Found {len(items)} results for Jumbo Loan search")
                
                for item in items:
                    snippet = item.get("snippet", "")
                    title = item.get("title", "")
                    text = f"{title} {snippet}".lower()
                    
                    # Extract rate percentage
                    if "jumbo" in text and ("7" in text or "arm" in text or "adjustable" in text):
                        # Look for percentage patterns: 6.5%, 6.50%, etc.
                        rate_patterns = [
                            r'(\d{1,2}\.?\d{0,2})\s*%',  # 6.5% or 6.50%
                            r'rate[:\s]+(\d{1,2}\.?\d{0,2})',  # rate: 6.5
                            r'(\d{1,2}\.?\d{0,2})\s*percent',  # 6.5 percent
                        ]
                        
                        for pattern in rate_patterns:
                            rate_match = re.search(pattern, text, re.IGNORECASE)
                            if rate_match:
                                rate_str = rate_match.group(1)
                                try:
                                    rate = float(rate_str)
                                    if 3.0 <= rate <= 10.0:  # Reasonable rate range
                                        result["rate"] = round(rate, 2)
                                        result["data_freshness"] = "fresh"
                                        print(f"Found Jumbo 7/1 ARM rate: {rate}%")
                                        break
                                except:
                                    pass
                        if result["rate"] > 0:
                            break
            except Exception as e:
                print(f"Error fetching loan rate for query '{query}': {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # If no data found, use placeholder
        if result["rate"] == 0.0:
            result = {
                "rate": 6.5,
                "data_freshness": "placeholder",
                "updated_at": datetime.now(pytz.UTC).isoformat(),
                "note": "数据暂不可用，显示示例数据。"
            }
        
    except Exception as e:
        print(f"Error fetching loan rate: {e}")
        import traceback
        traceback.print_exc()
        # Set placeholder on error
        result = {
            "rate": 6.5,
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。"
        }
    
    # Cache for 4 hours
    if redis_client:
        import json
        redis_client.setex(get_loan_cache_key(), 14400, json.dumps(result))
    
    return result

