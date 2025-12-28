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

redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None


def get_cache_key(query: str, start: int = 1) -> str:
    """Generate cache key for search query"""
    key_str = f"google_search:{query}:{start}"
    return hashlib.md5(key_str.encode()).hexdigest()


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
    
    # Check cache
    cache_key = get_cache_key(query, start)
    if use_cache and redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    
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
            
            # Cache for 10 minutes
            if use_cache and redis_client:
                redis_client.setex(cache_key, 600, json.dumps(data))
            
            return data
    except httpx.HTTPStatusError as e:
        error_msg = f"Error calling Google Search API: {e}"
        # Try to get detailed error message
        try:
            error_data = e.response.json()
            if "error" in error_data:
                error_info = error_data["error"]
                error_msg += f"\n  Error: {error_info.get('message', 'Unknown error')}"
                if "errors" in error_info:
                    for err in error_info["errors"]:
                        error_msg += f"\n  - {err.get('message', '')}"
        except:
            error_msg += f"\n  Response: {e.response.text[:200]}"
        print(error_msg)
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

