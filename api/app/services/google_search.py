import httpx
import os
import json
import redis
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import hashlib

GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
GOOGLE_CSE_ENDPOINT = os.getenv("GOOGLE_CSE_ENDPOINT", "https://www.googleapis.com/customsearch/v1")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DAILY_CSE_BUDGET = int(os.getenv("DAILY_CSE_BUDGET", "80"))

redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None


def get_daily_usage_key() -> str:
    """Get Redis key for today's usage counter"""
    today = datetime.now().strftime("%Y%m%d")
    return f"cse:usage:{today}"


def get_cache_key(query: str, date_restrict: Optional[str], start: int, num: int) -> str:
    """Generate cache key: cse:cache:<hash(q + dateRestrict + start + num)>"""
    key_str = f"{query}:{date_restrict or ''}:{start}:{num}"
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    return f"cse:cache:{key_hash}"


def check_budget_exceeded() -> bool:
    """Check if daily CSE budget has been exceeded"""
    if not redis_client:
        return False
    usage_key = get_daily_usage_key()
    current_usage = redis_client.get(usage_key)
    if current_usage is None:
        return False
    try:
        return int(current_usage) >= DAILY_CSE_BUDGET
    except (ValueError, TypeError):
        return False


def increment_usage() -> int:
    """Increment daily usage counter and return current count"""
    if not redis_client:
        return 0
    usage_key = get_daily_usage_key()
    # Set expiration to end of day (86400 seconds = 24 hours)
    # But we'll set it to 25 hours to be safe
    current = redis_client.incr(usage_key)
    if current == 1:
        # First increment today, set expiration
        redis_client.expire(usage_key, 90000)  # 25 hours
    return current


def search_google(
    query: str,
    site_domain: Optional[str] = None,
    num: int = 10,
    start: int = 1,
    date_restrict: Optional[str] = None,
    use_cache: bool = True
) -> Dict:
    """
    Search Google Custom Search API
    
    Args:
        query: Search query string
        site_domain: Optional site domain for siteSearch parameter
        num: Number of results (max 10)
        start: Start index for pagination
        date_restrict: Date restriction (e.g., "d7" for last 7 days)
        use_cache: Whether to use Redis cache
    
    Returns:
        Dict with search results
    """
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        print("WARNING: Google CSE API key or ID not set. Returning mock data.")
        return {
            "items": [
                {
                    "title": f"Mock Result {i}",
                    "link": f"https://example.com/article{i}",
                    "snippet": f"Mock snippet for query: {query}"
                }
                for i in range(1, min(num + 1, 6))
            ],
            "searchInformation": {"totalResults": "5"}
        }
    
    # Check cache first (cache hits don't consume budget)
    cache_key = get_cache_key(query, date_restrict, start, num)
    if use_cache and redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    
    # Check budget before making API call
    if check_budget_exceeded():
        print(f"WARNING: Daily CSE budget ({DAILY_CSE_BUDGET}) exceeded. Skipping query: {query}")
        return {
            "items": [],
            "searchInformation": {"totalResults": "0"},
            "error": "quota_exceeded"
        }
    
    # Prepare query - remove site: if siteSearch is used
    search_query = query
    if site_domain and "site:" in query.lower():
        # Remove site: operator if using siteSearch param
        import re
        search_query = re.sub(r'site:\S+\s*', '', query, flags=re.IGNORECASE).strip()
    
    params = {
        "key": GOOGLE_CSE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": search_query,
        "num": min(num, 10),
        "start": start
    }
    
    if site_domain:
        params["siteSearch"] = site_domain
    
    if date_restrict:
        params["dateRestrict"] = date_restrict
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(GOOGLE_CSE_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Increment usage counter (only on successful API call)
            usage_count = increment_usage()
            print(f"CSE API call #{usage_count}/{DAILY_CSE_BUDGET} for query: {query[:50]}...")
            
            # Cache for 30 minutes (1800 seconds)
            if use_cache and redis_client:
                redis_client.setex(cache_key, 1800, json.dumps(data))
            
            return data
    except httpx.HTTPStatusError as e:
        error_msg = f"Error calling Google Search API: {e}"
        is_quota_exceeded = False
        
        # Try to get detailed error message
        try:
            error_data = e.response.json()
            if "error" in error_data:
                error_info = error_data["error"]
                error_msg += f"\n  Error: {error_info.get('message', 'Unknown error')}"
                if "errors" in error_info:
                    for err in error_info["errors"]:
                        err_msg = err.get('message', '')
                        error_msg += f"\n  - {err_msg}"
                        # Check for quota exceeded
                        if "429" in str(e.response.status_code) or "quota" in err_msg.lower() or "too many requests" in err_msg.lower():
                            is_quota_exceeded = True
        except:
            error_msg += f"\n  Response: {e.response.text[:200]}"
            if e.response.status_code == 429:
                is_quota_exceeded = True
        
        print(error_msg)
        
        # If quota exceeded (429), increment usage to track it
        if is_quota_exceeded:
            increment_usage()
            print("WARNING: Google CSE API returned 429 error. Incrementing usage counter.")
        
        # Return empty results on error
        return {
            "items": [],
            "searchInformation": {"totalResults": "0"},
            "error": "quota_exceeded" if is_quota_exceeded else error_msg
        }
    except Exception as e:
        print(f"Error calling Google Search API: {e}")
        # Return mock data on error
        return {
            "items": [
                {
                    "title": f"Error Result {i}",
                    "link": f"https://example.com/error{i}",
                    "snippet": f"Error fetching: {query}"
                }
                for i in range(1, min(num + 1, 3))
            ],
            "searchInformation": {"totalResults": "0"}
        }


def fetch_multiple_pages(
    query: str,
    site_domain: Optional[str] = None,
    max_results: int = 30,
    date_restrict: Optional[str] = None
) -> List[Dict]:
    """
    Fetch multiple pages of results (Google limits to 10 per page)
    
    Args:
        query: Search query
        site_domain: Optional site domain
        max_results: Maximum number of results to fetch
        date_restrict: Date restriction
    
    Returns:
        List of result items
    """
    all_items = []
    start = 1
    page_size = 10
    
    while len(all_items) < max_results:
        results = search_google(
            query=query,
            site_domain=site_domain,
            num=page_size,
            start=start,
            date_restrict=date_restrict
        )
        
        # Check for quota exceeded error
        if results.get("error") == "quota_exceeded":
            print(f"WARNING: Budget exceeded during pagination. Returning {len(all_items)} items.")
            break
        
        # Check for other errors
        if results.get("error"):
            print(f"Error fetching page {start}: {results.get('error')}")
            break
        
        items = results.get("items", [])
        if not items:
            break
        
        all_items.extend(items)
        
        if len(items) < page_size:
            break
        
        start += page_size
        
        # Limit to avoid excessive API calls
        if start > 100:  # Google API limit
            break
    
    return all_items[:max_results]

