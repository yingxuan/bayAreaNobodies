"""
Powerball service - fetch real-time Powerball jackpot and next drawing time
Uses Google CSE to find Powerball information
"""
import os
import re
from typing import Dict, Optional
from datetime import datetime
import pytz
from app.services.google_search import search_google, check_budget_exceeded
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None


def get_powerball_cache_key() -> str:
    """Get Redis key for Powerball cache"""
    return "powerball:info"


def fetch_powerball_info() -> Dict:
    """
    Fetch Powerball information using Google CSE
    Returns current jackpot amount and next drawing time
    """
    # Check cache first (cache for 1 hour)
    if redis_client:
        cached = redis_client.get(get_powerball_cache_key())
        if cached:
            import json
            try:
                return json.loads(cached)
            except:
                pass
    
    # Check budget before making API call
    budget_exceeded = check_budget_exceeded()
    if budget_exceeded:
        # Return stale data if available
        if redis_client:
            cached = redis_client.get(get_powerball_cache_key())
            if cached:
                import json
                try:
                    data = json.loads(cached)
                    data["data_freshness"] = "stale_due_to_quota"
                    return data
                except:
                    pass
        # If no cache and budget exceeded, return placeholder data
        return {
            "jackpot": "$33M",
            "next_drawing": None,
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。请稍后刷新。"
        }
    
    # Try to fetch from Powerball official API or use a more reliable method
    jackpot_amount = "$0"
    next_drawing = None
    
    # First, try using a public API if available
    try:
        import httpx
        # Try Powerball official site or a reliable source
        # For now, we'll use Google CSE but with better queries
        pass
    except:
        pass
    
    # Search for Powerball information using Google CSE
    queries = [
        "powerball jackpot amount today",
        "site:powerball.com current jackpot",
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
            
            print(f"Found {len(items)} results for Powerball search")
            
            for item in items:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                text = f"{title} {snippet}".lower()
                
                # Extract Powerball jackpot - be more aggressive
                if "powerball" in text or "power ball" in text:
                    # More flexible regex patterns - prioritize smaller amounts (like 33M)
                    amount_patterns = [
                        r'jackpot[:\s]+\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*[bm]',  # jackpot: $33M
                        r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*[bm]illion',  # $33 Million
                        r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*[bm]',  # $33M
                        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*million',  # 33 million
                        r'jackpot[:\s]+\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # jackpot: $33
                    ]
                    
                    for pattern in amount_patterns:
                        pb_match = re.search(pattern, text, re.IGNORECASE)
                        if pb_match:
                            amount_str = pb_match.group(1).replace(',', '')
                            try:
                                amount = float(amount_str)
                                if amount > 0:
                                    # Format: if >= 1000, show as billions, else millions
                                    if amount >= 1000:
                                        jackpot_amount = f"${amount/1000:.1f}B"
                                    else:
                                        jackpot_amount = f"${int(amount)}M"
                                    print(f"Found Powerball jackpot: {jackpot_amount} from {link}")
                                    break
                            except:
                                pass
                    if jackpot_amount != "$0":
                        break
                    
                    # Extract next drawing time
                    drawing_patterns = [
                        r'next drawing[:\s]+([a-z]+\s+\d{1,2}(?:\s+\d{4})?)',
                        r'drawing on[:\s]+([a-z]+\s+\d{1,2}(?:\s+\d{4})?)',
                        r'(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)',
                    ]
                    for pattern in drawing_patterns:
                        drawing_match = re.search(pattern, text, re.IGNORECASE)
                        if drawing_match:
                            next_drawing = drawing_match.group(1)
                            print(f"Found next drawing: {next_drawing}")
                            break
        except Exception as e:
            print(f"Error fetching Powerball info for query '{query}': {e}")
            import traceback
            traceback.print_exc()
            continue
    
    result = {
        "jackpot": jackpot_amount,
        "next_drawing": next_drawing,
        "data_freshness": "fresh" if jackpot_amount != "$0" else "no_data",
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    # If no data found and budget not exceeded, use placeholder
    if jackpot_amount == "$0" and not budget_exceeded:
        result = {
            "jackpot": "$33M",
            "next_drawing": None,
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。"
        }
    elif jackpot_amount == "$0":
        # Budget exceeded, return placeholder
        result = {
            "jackpot": "$33M",
            "next_drawing": None,
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。"
        }
    
    # Cache for 1 hour
    if redis_client:
        import json
        redis_client.setex(get_powerball_cache_key(), 3600, json.dumps(result))
    
    return result

