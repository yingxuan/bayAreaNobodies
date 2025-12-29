"""
Boba/Milk Tea Service - specialized service for Chinese-style boba recommendations
Improved search, filtering, and ranking for popular Chinese boba shops
"""
import os
import redis
import json
import math
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import httpx

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Monta Vista High School coordinates (Cupertino)
MONTA_VISTA_LAT = 37.3206
MONTA_VISTA_LNG = -122.0444

# Search configuration
INITIAL_RADIUS_M = 5000  # 5km
MAX_DISTANCE_MILES = 5.0

# Preferred Chinese boba brands (boost these in ranking)
PREFERRED_BRANDS = [
    "TP Tea", "Tea Top", "YiFang", "Gong Cha", "Tiger Sugar", "Sunright",
    "Chicha San Chen", "Happy Lemon", "Boba Guys", "One Zo", "Sharetea",
    "Teaspoon", "Ten Ren", "T4", "Boba Time", "Tea Station", "Quickly",
    "CoCo", "Kung Fu Tea", "Vivi Bubble Tea", "Chatime", "Ding Tea"
]

# Boba-related keywords (must match at least one)
BOBA_KEYWORDS = [
    "boba", "bubble tea", "milk tea", "pearl milk tea", "taiwanese tea",
    "奶茶", "珍珠奶茶", "波霸", "水果茶", "芝士茶", "手摇茶"
]

# Exclusion keywords (filter out if name contains these)
EXCLUSION_KEYWORDS = [
    "starbucks", "peet's", "peets", "coffee", "cafe", "bakery", "donut",
    "dunkin", "caribou", "blue bottle", "philz", "peets coffee"
]

# Search queries for multi-query approach
BOBA_SEARCH_QUERIES = [
    "boba near Monta Vista High School Cupertino",
    "bubble tea near Monta Vista High School Cupertino",
    "milk tea near Monta Vista High School Cupertino",
    "taiwanese tea near Monta Vista High School Cupertino",
    "奶茶 near Monta Vista High School Cupertino",
    "珍珠奶茶 near Monta Vista High School Cupertino"
]


def get_boba_cache_key() -> str:
    """Get Redis key for boba recommendations cache"""
    return "boba:recommendations:monta_vista"


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles using Haversine formula"""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def is_boba_place(place: Dict) -> bool:
    """
    Check if a place is a Chinese-style boba shop
    Filters out generic cafes and coffee shops
    """
    name = (place.get("name", "") or "").lower()
    types = place.get("types", [])
    types_lower = [t.lower() for t in types]
    
    # Exclude if name contains exclusion keywords (but allow if it also has boba keywords)
    has_exclusion = any(exclusion in name for exclusion in EXCLUSION_KEYWORDS)
    has_boba_in_name = any(keyword in name for keyword in BOBA_KEYWORDS)
    
    # If it has exclusion keywords but no boba keywords, exclude it
    if has_exclusion and not has_boba_in_name:
        return False
    
    # Must contain at least one boba keyword in name or types
    name_has_boba = any(keyword in name for keyword in BOBA_KEYWORDS)
    types_has_boba = any(
        any(keyword in t for keyword in BOBA_KEYWORDS)
        for t in types_lower
    )
    
    if name_has_boba or types_has_boba:
        return True
    
    # If it's a cafe, check more carefully
    if "cafe" in types_lower or "coffee_shop" in types_lower:
        # Check if it has tea-related types or is a beverage store
        tea_types = ["tea", "bubble_tea", "beverage_store", "food", "meal_takeaway"]
        if any(tea_type in types_lower for tea_type in tea_types):
            # If it's a cafe with tea types, include it (might be a boba cafe)
            return True
    
    # Also check for preferred brands (even if no explicit boba keyword)
    for brand in PREFERRED_BRANDS:
        if brand.lower() in name:
            return True
    
    return False


def calculate_popularity_score(place: Dict, distance_miles: float) -> float:
    """
    Calculate popularity score for ranking
    score = (rating * log1p(user_ratings_total)) + name_keyword_boost - distance_penalty
    """
    rating = place.get("rating", 0) or 0
    user_ratings_total = place.get("user_ratings_total", 0) or 0
    name = (place.get("name", "") or "").lower()
    is_open = place.get("opening_hours", {}).get("open_now", False)
    
    # Base popularity score
    if user_ratings_total > 0:
        base_score = rating * math.log1p(user_ratings_total)
    else:
        base_score = rating * 0.5  # Penalize places with no reviews
    
    # Name keyword boost (stronger match = higher boost)
    name_keyword_boost = 0.0
    for keyword in BOBA_KEYWORDS:
        if keyword in name:
            # Exact match gets higher boost
            if f" {keyword} " in f" {name} " or name.startswith(keyword) or name.endswith(keyword):
                name_keyword_boost += 2.0
            else:
                name_keyword_boost += 1.0
    
    # Preferred brand boost
    brand_boost = 0.0
    for brand in PREFERRED_BRANDS:
        if brand.lower() in name:
            brand_boost += 5.0  # Strong boost for known brands
            break
    
    # Open now boost (small)
    open_boost = 0.5 if is_open else 0.0
    
    # Distance penalty (small, prioritize popularity over distance)
    distance_penalty = distance_miles * 0.2
    
    total_score = base_score + name_keyword_boost + brand_boost + open_boost - distance_penalty
    
    return total_score


async def search_boba_places() -> List[Dict]:
    """
    Search for boba places using multiple queries
    Returns deduplicated list of places
    """
    if not GOOGLE_MAPS_API_KEY:
        return []
    
    location = f"{MONTA_VISTA_LAT},{MONTA_VISTA_LNG}"
    all_places = {}
    seen_place_ids = set()
    
    async with httpx.AsyncClient() as client:
        for query in BOBA_SEARCH_QUERIES:
            try:
                search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
                search_params = {
                    "query": query,
                    "key": GOOGLE_MAPS_API_KEY,
                    "location": location,
                    "radius": INITIAL_RADIUS_M
                }
                
                response = await client.get(search_url, params=search_params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "OK":
                    results = data.get("results", [])
                    for place in results:
                        place_id = place.get("place_id")
                        if place_id and place_id not in seen_place_ids:
                            seen_place_ids.add(place_id)
                            all_places[place_id] = place
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"Error in boba search query '{query}': {e}")
                continue
    
    return list(all_places.values())


async def get_place_details(place_id: str) -> Optional[Dict]:
    """Get detailed place information"""
    if not GOOGLE_MAPS_API_KEY:
        return None
    
    try:
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            "place_id": place_id,
            "key": GOOGLE_MAPS_API_KEY,
            "fields": "name,formatted_address,formatted_phone_number,rating,user_ratings_total,price_level,opening_hours,geometry,photos,url,types,editorial_summary"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(details_url, params=details_params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK":
                return data.get("result")
    except Exception as e:
        print(f"Error fetching place details for {place_id}: {e}")
    
    return None


async def fetch_boba_recommendations(limit: int = 12) -> List[Dict]:
    """
    Fetch and rank Chinese-style boba recommendations near Monta Vista High School
    Returns top N places sorted by popularity score
    """
    # Check cache first (6 hours TTL)
    if redis_client:
        cached = redis_client.get(get_boba_cache_key())
        if cached:
            try:
                data = json.loads(cached)
                # Return cached results if available
                return data.get("places", [])[:limit]
            except:
                pass
    
    if not GOOGLE_MAPS_API_KEY:
        return []
    
    try:
        # Search for boba places
        print(f"[Boba Service] Searching for boba places near Monta Vista HS...")
        places = await search_boba_places()
        print(f"[Boba Service] Found {len(places)} unique places from search")
        
        # Filter and get details
        boba_places = []
        for place in places:
            if is_boba_place(place):
                place_id = place.get("place_id")
                if place_id:
                    # Get full details
                    details = await get_place_details(place_id)
                    if details:
                        # Calculate distance
                        geometry = details.get("geometry", {})
                        location = geometry.get("location", {})
                        place_lat = location.get("lat")
                        place_lng = location.get("lng")
                        
                        if place_lat and place_lng:
                            distance_miles = calculate_distance(
                                MONTA_VISTA_LAT, MONTA_VISTA_LNG,
                                place_lat, place_lng
                            )
                            
                            if distance_miles <= MAX_DISTANCE_MILES:
                                # Calculate popularity score
                                score = calculate_popularity_score(details, distance_miles)
                                
                                # Get photo URL
                                photo_url = None
                                if details.get("photos"):
                                    photo_ref = details["photos"][0].get("photo_reference")
                                    if photo_ref:
                                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={GOOGLE_MAPS_API_KEY}"
                                
                                boba_places.append({
                                    "place_id": place_id,
                                    "name": details.get("name", ""),
                                    "address": details.get("formatted_address", ""),
                                    "phone": details.get("formatted_phone_number"),
                                    "rating": details.get("rating"),
                                    "user_ratings_total": details.get("user_ratings_total"),
                                    "price_level": details.get("price_level"),
                                    "google_maps_url": details.get("url"),
                                    "photo_url": photo_url,
                                    "is_open_now": details.get("opening_hours", {}).get("open_now"),
                                    "distance_miles": round(distance_miles, 2),
                                    "score": score,
                                    "types": details.get("types", [])
                                })
        
        # Sort by popularity score (descending)
        boba_places.sort(key=lambda p: p["score"], reverse=True)
        
        # Log top results for debugging
        print(f"[Boba Service] Filtered to {len(boba_places)} boba places")
        for i, place in enumerate(boba_places[:10], 1):
            print(f"[Boba Service] #{i}: {place['name']} - Score: {place['score']:.2f}, Rating: {place['rating']}, Reviews: {place['user_ratings_total']}, Distance: {place['distance_miles']}mi")
        
        # Cache results
        if redis_client:
            cache_data = {
                "places": boba_places,
                "cached_at": datetime.now().isoformat()
            }
            redis_client.setex(get_boba_cache_key(), 21600, json.dumps(cache_data))  # 6 hours
        
        return boba_places[:limit]
        
    except Exception as e:
        print(f"Error in fetch_boba_recommendations: {e}")
        import traceback
        traceback.print_exc()
        
        # Return cached data if available
        if redis_client:
            cached = redis_client.get(get_boba_cache_key())
            if cached:
                try:
                    data = json.loads(cached)
                    return data.get("places", [])[:limit]
                except:
                    pass
        
        return []

