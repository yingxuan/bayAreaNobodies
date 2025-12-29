"""
Service for "今天吃什么" (Today's Food Pick) feature
Randomly selects a Chinese restaurant and finds its best dish
"""
import os
import httpx
import json
import redis
import hashlib
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from app.models import Restaurant

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None


def get_cache_key(city: str, date_str: str) -> str:
    """Get Redis cache key for today's pick"""
    return f"food:today:{city}:{date_str}"


def get_lock_key(city: str, date_str: str) -> str:
    """Get Redis lock key to prevent cache stampede"""
    return f"food:today:lock:{city}:{date_str}"


def acquire_lock(city: str, date_str: str, timeout: int = 10) -> bool:
    """Acquire distributed lock"""
    if not redis_client:
        return True  # No Redis, assume lock acquired
    
    lock_key = get_lock_key(city, date_str)
    try:
        # Try to set lock with expiration
        result = redis_client.set(lock_key, "1", ex=timeout, nx=True)
        return result is True
    except:
        return True  # On error, assume lock acquired


def release_lock(city: str, date_str: str):
    """Release distributed lock"""
    if not redis_client:
        return
    
    lock_key = get_lock_key(city, date_str)
    try:
        redis_client.delete(lock_key)
    except:
        pass


def get_daily_seed(city: str, date_str: str) -> int:
    """Generate deterministic seed for daily random selection"""
    seed_string = f"{city}:{date_str}"
    seed_hash = hashlib.md5(seed_string.encode()).hexdigest()
    # Convert first 8 chars to int for seed
    return int(seed_hash[:8], 16)


def select_restaurant_for_today(db: Session, city: str, date_str: str) -> Optional[Restaurant]:
    """
    Select a random Chinese restaurant for today (deterministic based on date)
    """
    try:
        # Get all Chinese restaurants
        restaurants = db.query(Restaurant).filter(
            Restaurant.cuisine_type == "chinese"
        ).all()
        
        if not restaurants:
            return None
        
        # Use date-based seed for deterministic selection
        import random
        seed = get_daily_seed(city, date_str)
        random.seed(seed)
        
        # Randomly select one restaurant
        selected = random.choice(restaurants)
        return selected
    except Exception as e:
        print(f"Error selecting restaurant: {e}")
        return None


def extract_dish_from_reviews(reviews: List[Dict]) -> Optional[str]:
    """
    Extract dish name from Google Places reviews
    Looks for common patterns like "推荐", "必点", "招牌", dish names
    """
    if not reviews:
        return None
    
    # Common dish keywords in Chinese
    dish_keywords = [
        "红烧肉", "宫保鸡丁", "麻婆豆腐", "水煮鱼", "回锅肉", "糖醋排骨",
        "小笼包", "生煎包", "担担面", "牛肉面", "酸菜鱼", "口水鸡",
        "烤鸭", "白切鸡", "叉烧", "烧鹅", "蒸蛋", "炒饭", "炒面",
        "火锅", "麻辣烫", "串串", "烧烤", "烤鱼", "小龙虾"
    ]
    
    # Look through reviews for dish mentions
    for review in reviews[:10]:  # Check top 10 reviews
        text = review.get("text", "").lower()
        
        # Check for dish keywords
        for keyword in dish_keywords:
            if keyword in text:
                return keyword
        
        # Check for recommendation patterns
        if any(word in text for word in ["推荐", "必点", "招牌", "最好", "最爱"]):
            # Try to extract dish name from context
            # Simple heuristic: look for common dish patterns
            for keyword in dish_keywords:
                if keyword in text:
                    return keyword
    
    return None


def get_restaurant_dish(restaurant: Restaurant) -> Dict:
    """
    Get the best dish for a restaurant
    Priority: Google Places reviews -> fallback to "招牌菜"
    """
    dish_name = "招牌菜"
    dish_image = restaurant.photo_url  # Fallback to restaurant photo
    
    # Try to get dish from Google Places reviews
    if GOOGLE_MAPS_API_KEY and restaurant.place_id:
        try:
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            details_params = {
                "place_id": restaurant.place_id,
                "key": GOOGLE_MAPS_API_KEY,
                "fields": "reviews,photos"
            }
            
            with httpx.Client(timeout=5.0) as client:
                response = client.get(details_url, params=details_params)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK":
                        result = data.get("result", {})
                        
                        # Try to extract dish from reviews
                        reviews = result.get("reviews", [])
                        extracted_dish = extract_dish_from_reviews(reviews)
                        if extracted_dish:
                            dish_name = extracted_dish
                        
                        # Try to get a food photo (not restaurant exterior)
                        photos = result.get("photos", [])
                        if photos and len(photos) > 1:
                            # Use second photo (often food, first is usually exterior)
                            photo_ref = photos[1].get("photo_reference")
                            if photo_ref:
                                dish_image = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_ref}&key={GOOGLE_MAPS_API_KEY}"
        except Exception as e:
            print(f"Error fetching dish info from Google Places: {e}")
    
    return {
        "name": dish_name,
        "image": dish_image
    }


def fetch_today_pick(city: str = "cupertino", db: Session = None) -> Dict:
    """
    Get today's food pick (restaurant + dish)
    Returns cached result if available, otherwise generates new pick
    """
    # Get today's date string
    today = datetime.now(pytz.UTC)
    date_str = today.strftime("%Y-%m-%d")
    
    cache_key = get_cache_key(city, date_str)
    
    # Check cache first
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    # Acquire lock to prevent cache stampede
    if not acquire_lock(city, date_str):
        # If lock exists, wait a bit and try cache again
        import time
        time.sleep(0.5)
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass
        # If still no cache, return mock
        return get_mock_today_pick(city, date_str)
    
    try:
        # Select restaurant for today
        if not db:
            return get_mock_today_pick(city, date_str)
        
        restaurant = select_restaurant_for_today(db, city, date_str)
        
        if not restaurant:
            return get_mock_today_pick(city, date_str)
        
        # Get dish information
        dish = get_restaurant_dish(restaurant)
        
        # Build Google Maps URL
        google_maps_url = restaurant.google_maps_url
        if not google_maps_url and restaurant.place_id:
            google_maps_url = f"https://maps.google.com/?q=place_id:{restaurant.place_id}"
        
        result = {
            "city": city,
            "date": date_str,
            "restaurant": {
                "name": restaurant.name or "未知餐厅",
                "googlePlaceId": restaurant.place_id or "",
                "googleMapsUrl": google_maps_url or "",
                "rating": restaurant.rating or 0.0
            },
            "dish": {
                "name": dish["name"],
                "image": dish["image"] or restaurant.photo_url or ""
            },
            "dataSource": "google_places",
            "stale": False,
            "ttlSeconds": 86400,  # 24 hours
            "updatedAt": today.isoformat()
        }
        
        # Cache for 24 hours
        if redis_client:
            redis_client.setex(cache_key, 86400, json.dumps(result, default=str))
        
        return result
        
    except Exception as e:
        print(f"Error in fetch_today_pick: {e}")
        import traceback
        traceback.print_exc()
        return get_mock_today_pick(city, date_str)
    finally:
        release_lock(city, date_str)


def get_mock_today_pick(city: str, date_str: str) -> Dict:
    """Return mock data as fallback"""
    today = datetime.now(pytz.UTC)
    
    # Use date-based seed for consistent mock data
    import random
    seed = get_daily_seed(city, date_str)
    random.seed(seed)
    
    mock_restaurants = [
        {"name": "Home Eat 汉家宴", "rating": 4.7},
        {"name": "川味轩", "rating": 4.5},
        {"name": "上海人家", "rating": 4.6},
        {"name": "湘味园", "rating": 4.4},
        {"name": "东北饺子王", "rating": 4.3}
    ]
    
    mock_dishes = [
        "招牌红烧肉",
        "宫保鸡丁",
        "麻婆豆腐",
        "水煮鱼",
        "糖醋排骨"
    ]
    
    selected_restaurant = random.choice(mock_restaurants)
    selected_dish = random.choice(mock_dishes)
    
    return {
        "city": city,
        "date": date_str,
        "restaurant": {
            "name": selected_restaurant["name"],
            "googlePlaceId": "",
            "googleMapsUrl": f"https://maps.google.com/?q={selected_restaurant['name']}+{city}",
            "rating": selected_restaurant["rating"]
        },
        "dish": {
            "name": selected_dish,
            "image": ""
        },
        "dataSource": "mock",
        "stale": True,
        "ttlSeconds": 86400,
        "updatedAt": today.isoformat()
    }

