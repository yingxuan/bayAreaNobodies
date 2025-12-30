"""
Metadata API endpoints for extracting OG images and favicons
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import redis
import json
import os
from typing import Optional

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 24 hours
METADATA_CACHE_TTL = 86400

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_cache_key(url: str) -> str:
    """Get Redis cache key for metadata"""
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return f"metadata:{url_hash}"


def extract_favicon(html: str, base_url: str) -> Optional[str]:
    """Extract favicon URL from HTML"""
    soup = BeautifulSoup(html, 'lxml')
    
    # Try various favicon selectors
    favicon_selectors = [
        'link[rel="icon"]',
        'link[rel="shortcut icon"]',
        'link[rel="apple-touch-icon"]',
        'link[rel="apple-touch-icon-precomposed"]'
    ]
    
    for selector in favicon_selectors:
        elem = soup.select_one(selector)
        if elem and elem.get('href'):
            href = elem.get('href')
            # Resolve relative URLs
            if href.startswith('http://') or href.startswith('https://'):
                return href
            return urljoin(base_url, href)
    
    # Fallback: try /favicon.ico
    try:
        parsed = urlparse(base_url)
        favicon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
        return favicon_url
    except:
        pass
    
    return None


def extract_og_image(html: str, base_url: str) -> Optional[str]:
    """Extract OG image from HTML"""
    soup = BeautifulSoup(html, 'lxml')
    
    # Try og:image
    og_image = soup.find('meta', property='og:image')
    if og_image and og_image.get('content'):
        href = og_image.get('content')
        if href.startswith('http://') or href.startswith('https://'):
            return href
        return urljoin(base_url, href)
    
    # Try twitter:image
    twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
    if twitter_image and twitter_image.get('content'):
        href = twitter_image.get('content')
        if href.startswith('http://') or href.startswith('https://'):
            return href
        return urljoin(base_url, href)
    
    return None


@router.get("/metadata")
def get_metadata(
    url: str = Query(..., description="URL to extract metadata from")
):
    """
    Extract metadata (OG image, favicon) from a URL
    Returns cached results if available
    """
    if not url or not url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid URL")
    
    cache_key = get_cache_key(url)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            
            og_image = extract_og_image(html, url)
            favicon = extract_favicon(html, url)
            
            result = {
                "url": url,
                "og_image": og_image,
                "favicon": favicon,
                "image": og_image or favicon  # Prefer OG image, fallback to favicon
            }
            
            # Cache result
            if redis_client:
                redis_client.setex(cache_key, METADATA_CACHE_TTL, json.dumps(result))
            
            return result
            
    except Exception as e:
        print(f"Error fetching metadata for {url}: {e}")
        # Return empty result (will use placeholder)
        result = {
            "url": url,
            "og_image": None,
            "favicon": None,
            "image": None
        }
        
        # Cache error result (shorter TTL: 1 hour)
        if redis_client:
            redis_client.setex(cache_key, 3600, json.dumps(result))
        
        return result

