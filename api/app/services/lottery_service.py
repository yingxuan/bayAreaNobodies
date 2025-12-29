"""
CA Lottery service - fetch current jackpot amounts
Uses Google CSE to find CA lottery official information
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


def get_lottery_cache_key() -> str:
    """Get Redis key for lottery cache"""
    return "lottery:ca:info"


def fetch_lottery_info() -> Dict:
    """
    Fetch CA lottery information using Google CSE
    Returns current jackpot amounts for Mega Millions, Powerball, SuperLotto Plus
    """
    # Check cache first (cache for 1 hour)
    if redis_client:
        cached = redis_client.get(get_lottery_cache_key())
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
            cached = redis_client.get(get_lottery_cache_key())
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
            "jackpot": {
                "mega_millions": {"amount": "$70M", "next_drawing": None},
                "powerball": {"amount": "$659M", "next_drawing": None},
                "super_lotto_plus": {"amount": "$11M", "next_drawing": None}
            },
            "recent_winners": [],
            "data_freshness": "placeholder",
            "updated_at": datetime.now(pytz.UTC).isoformat(),
            "note": "数据暂不可用，显示示例数据。请稍后刷新。"
        }
    
    # Search for CA lottery information
    queries = [
        "site:calottery.com jackpot amounts",
        "California lottery mega millions powerball jackpot",
    ]
    
    jackpot_info = {
        "mega_millions": {"amount": "$0", "next_drawing": None},
        "powerball": {"amount": "$0", "next_drawing": None},
        "super_lotto_plus": {"amount": "$0", "next_drawing": None}
    }
    
    for query in queries[:2]:  # Limit to 2 queries to save quota
        try:
            results = search_google(query, num=10, date_restrict="d1")
            if results.get("error"):
                print(f"Lottery search error for '{query}': {results.get('error')}")
                continue
            
            items = results.get("items", [])
            if not items:
                print(f"No results for query: {query}")
                continue
            
            for item in items:
                snippet = item.get("snippet", "")
                title = item.get("title", "")
                link = item.get("link", "")
                text = f"{title} {snippet}".lower()
                
                # More flexible regex patterns to match various formats
                # Patterns: $500M, $500 Million, 500M, 500 million, etc.
                amount_patterns = [
                    r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*[bm]illion',  # $500 Million, 500M
                    r'\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*[bm]',  # $500M, 500M
                    r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*million',  # 500 million
                ]
                
                # Extract Mega Millions
                if "mega millions" in text or "megamillions" in text:
                    for pattern in amount_patterns:
                        mm_match = re.search(pattern, text, re.IGNORECASE)
                        if mm_match:
                            amount_str = mm_match.group(1).replace(',', '')
                            try:
                                amount = float(amount_str)
                                if amount > 0:
                                    jackpot_info["mega_millions"]["amount"] = f"${int(amount)}M"
                                    print(f"Found Mega Millions: ${int(amount)}M from {link}")
                                    break
                            except:
                                pass
                
                # Extract Powerball
                if "powerball" in text or "power ball" in text:
                    for pattern in amount_patterns:
                        pb_match = re.search(pattern, text, re.IGNORECASE)
                        if pb_match:
                            amount_str = pb_match.group(1).replace(',', '')
                            try:
                                amount = float(amount_str)
                                if amount > 0:
                                    jackpot_info["powerball"]["amount"] = f"${int(amount)}M"
                                    print(f"Found Powerball: ${int(amount)}M from {link}")
                                    break
                            except:
                                pass
                
                # Extract SuperLotto Plus
                if "superlotto" in text or "super lotto" in text or "superlotto plus" in text:
                    for pattern in amount_patterns:
                        sl_match = re.search(pattern, text, re.IGNORECASE)
                        if sl_match:
                            amount_str = sl_match.group(1).replace(',', '')
                            try:
                                amount = float(amount_str)
                                if amount > 0:
                                    jackpot_info["super_lotto_plus"]["amount"] = f"${int(amount)}M"
                                    print(f"Found SuperLotto Plus: ${int(amount)}M from {link}")
                                    break
                            except:
                                pass
        except Exception as e:
            print(f"Error fetching lottery info for query '{query}': {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Check if we found any data
    all_zero = (
        jackpot_info["mega_millions"]["amount"] == "$0" and
        jackpot_info["powerball"]["amount"] == "$0" and
        jackpot_info["super_lotto_plus"]["amount"] == "$0"
    )
    
    result = {
        "jackpot": jackpot_info,
        "recent_winners": [],
        "data_freshness": "fresh" if not all_zero else "no_data",
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    # Cache for 1 hour (even if placeholder)
    if redis_client:
        import json
        redis_client.setex(get_lottery_cache_key(), 3600, json.dumps(result))
    
    return result

