"""
Food Deals Service - Fetch fast food deals using Google CSE
"""
import os
import json
import redis
from typing import List, Dict, Optional
from datetime import datetime
import pytz
from app.services.google_search import search_google, check_budget_exceeded

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 6 hours
CACHE_TTL = 21600

# Mock food deals (fallback)
MOCK_FOOD_DEALS = [
    {
        "id": "mock-bk-bogo",
        "title": "Burger King BOGO Whopper Deal",
        "description": "Buy one Whopper, get one free with coupon code",
        "url": "https://www.burgerking.com/promotions",
        "source": "burgerking.com",
        "category": "food_fast",
        "imageUrl": None,
        "saveAmount": None,
        "code": None
    },
    {
        "id": "mock-subway",
        "title": "Subway $5 Footlong Deal",
        "description": "Limited time $5 footlong sandwiches",
        "url": "https://www.subway.com/en-us/promotions",
        "source": "subway.com",
        "category": "food_fast",
        "imageUrl": None,
        "saveAmount": "5.00",
        "code": None
    },
    {
        "id": "mock-mcd",
        "title": "McDonald's App Deal - Free Fries",
        "description": "Download app and get free fries with purchase",
        "url": "https://www.mcdonalds.com/us/en-us/deals.html",
        "source": "mcdonalds.com",
        "category": "food_fast",
        "imageUrl": None,
        "saveAmount": None,
        "code": None
    }
]


def get_cache_key(city: str) -> str:
    """Get Redis cache key for food deals"""
    return f"deals:food:{city}"


def extract_image_from_result(result: Dict) -> Optional[str]:
    """Extract image URL from Google CSE result"""
    # Try pagemap.cse_image
    pagemap = result.get("pagemap", {})
    if pagemap:
        cse_images = pagemap.get("cse_image", [])
        if cse_images and len(cse_images) > 0:
            img_url = cse_images[0].get("src") or cse_images[0].get("url")
            if img_url and (img_url.startswith("http://") or img_url.startswith("https://")):
                return img_url
        
        cse_thumbnails = pagemap.get("cse_thumbnail", [])
        if cse_thumbnails and len(cse_thumbnails) > 0:
            img_url = cse_thumbnails[0].get("src") or cse_thumbnails[0].get("url")
            if img_url and (img_url.startswith("http://") or img_url.startswith("https://")):
                return img_url
    
    return None


def parse_deal_from_result(result: Dict) -> Optional[Dict]:
    """Parse a deal from Google CSE search result"""
    title = result.get("title", "")
    snippet = result.get("snippet", "")
    link = result.get("link", "")
    
    if not title or not link:
        return None
    
    # Extract brand
    brands = {
        "burger king": "Burger King",
        "bk": "Burger King",
        "mcdonald": "McDonald's",
        "mcd": "McDonald's",
        "subway": "Subway",
        "taco bell": "Taco Bell",
        "domino": "Domino's",
        "chipotle": "Chipotle",
        "pizza hut": "Pizza Hut",
        "kfc": "KFC"
    }
    
    brand = None
    text_lower = f"{title} {snippet}".lower()
    for key, value in brands.items():
        if key in text_lower:
            brand = value
            break
    
    # Extract deal type
    deal_type = None
    if "bogo" in text_lower or "buy one get one" in text_lower or "买一送一" in text_lower:
        deal_type = "BOGO"
    elif "% off" in text_lower or "discount" in text_lower:
        deal_type = "discount"
    elif "combo" in text_lower or "meal deal" in text_lower:
        deal_type = "combo"
    
    # Extract save amount (rough estimate)
    save_amount = None
    dollar_match = re.search(r'\$(\d+\.?\d*)', text_lower)
    if dollar_match:
        save_amount = dollar_match.group(1)
    
    # Extract image
    image_url = extract_image_from_result(result)
    
    # Generate title
    if brand:
        if deal_type == "BOGO":
            deal_title = f"{brand} BOGO Deal"
        elif save_amount:
            deal_title = f"{brand} Save ${save_amount} Deal"
        else:
            deal_title = f"{brand} Deal"
    else:
        deal_title = title[:60]  # Truncate if too long
    
    # Extract source domain
    try:
        from urllib.parse import urlparse
        parsed = urlparse(link)
        source = parsed.netloc.replace("www.", "")
    except:
        source = "unknown"
    
    return {
        "id": f"food-{hash(link) % 1000000}",  # Simple hash-based ID
        "title": deal_title,
        "description": snippet[:200] if snippet else "",
        "url": link,
        "source": source,
        "category": "food_fast",
        "imageUrl": image_url,
        "saveAmount": save_amount,
        "code": None
    }


def fetch_food_deals(city: str = "cupertino", limit: int = 10) -> List[Dict]:
    """
    Fetch fast food deals using Google CSE
    Returns list of deal objects
    """
    cache_key = get_cache_key(city)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    # Check budget
    if check_budget_exceeded():
        print("WARNING: CSE budget exceeded, returning mock food deals")
        return MOCK_FOOD_DEALS[:limit]
    
    # Search queries for fast food deals
    queries = [
        "Burger King BOGO coupon",
        "Subway coupon code",
        "McDonald's app deal",
        "Taco Bell deal today",
        "Domino's coupon",
        "fast food BOGO",
        "Chipotle promo code"
    ]
    
    all_deals = []
    seen_urls = set()
    
    for query in queries[:3]:  # Limit to 3 queries to save budget
        try:
            results = search_google(query, num=5, date_restrict="d7", use_cache=True)
            
            if results.get("error"):
                continue
            
            items = results.get("items", [])
            for item in items:
                link = item.get("link", "")
                if not link or link in seen_urls:
                    continue
                
                deal = parse_deal_from_result(item)
                if deal:
                    all_deals.append(deal)
                    seen_urls.add(link)
                    
                    if len(all_deals) >= limit:
                        break
            
            if len(all_deals) >= limit:
                break
                
        except Exception as e:
            print(f"Error searching for food deals with query '{query}': {e}")
            continue
    
    # If we got deals, cache them
    if all_deals and redis_client:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(all_deals, default=str))
        return all_deals
    
    # Fallback to mock
    return MOCK_FOOD_DEALS[:limit]

