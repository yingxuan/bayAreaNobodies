"""
Food-related endpoints for the food tab:
1. Restaurants from Google Maps (中餐, 日本菜, 韩国菜, 越南菜, 奶茶)
2. Check-in functionality
3. Explore posts from 1point3acres and huaren
4. Food blogger videos from YouTube
5. Today's food pick (今天吃什么)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from app.database import get_db
from app.models import Restaurant, CheckIn, Article, User
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os
import httpx
import json
import math

router = APIRouter()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


@router.get("/restaurants")
async def get_restaurants(
    cuisine_type: str = Query(..., description="chinese, japanese, korean, vietnamese, boba"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get restaurants from Google Maps Places API near Cupertino
    """
    if not GOOGLE_MAPS_API_KEY:
        # Return mock data if API key not configured
        mock_restaurants = []
        cuisine_names = {
            "chinese": ["川菜馆", "粤菜馆", "湘菜馆", "东北菜", "上海菜"],
            "japanese": ["寿司店", "拉面馆", "日式烧烤", "居酒屋", "日式料理"],
            "korean": ["韩式烧烤", "韩式料理", "韩国炸鸡", "韩式汤饭", "韩式火锅"],
            "vietnamese": ["越南粉", "越式料理", "越南菜", "越式春卷", "越式河粉"],
            "boba": ["奶茶店", "珍珠奶茶", "水果茶", "芝士茶", "波霸奶茶"]
        }
        names = cuisine_names.get(cuisine_type, ["示例餐厅"])
        for i, name in enumerate(names[:5], 1):
            mock_restaurants.append({
                "id": i,
                "place_id": f"mock_place_{cuisine_type}_{i}",
                "name": f"{name} {i}",
                "address": f"Cupertino, CA {i}",
                "phone": None,
                "rating": 4.0 + (i * 0.1),
                "user_ratings_total": 50 + (i * 10),
                "price_level": i % 4,
                "google_maps_url": f"https://www.google.com/maps/place/example{i}",
                "photo_url": None,
                "is_open_now": i % 2 == 0,
                "check_in_count": 0
            })
        return {"restaurants": mock_restaurants}
    
    # For boba, use specialized service
    if cuisine_type == "boba":
        from app.services.boba_service import fetch_boba_recommendations
        try:
            boba_places = await fetch_boba_recommendations(limit=limit)
            
            # Convert to restaurant format and save to DB
            restaurants = []
            for place_data in boba_places:
                place_id = place_data.get("place_id")
                if not place_id:
                    continue
                
                # Check if restaurant exists in DB
                restaurant = db.query(Restaurant).filter(Restaurant.place_id == place_id).first()
                
                if not restaurant:
                    restaurant = Restaurant(
                        place_id=place_id,
                        name=place_data.get("name", ""),
                        address=place_data.get("address"),
                        phone=place_data.get("phone"),
                        rating=place_data.get("rating"),
                        user_ratings_total=place_data.get("user_ratings_total"),
                        price_level=place_data.get("price_level"),
                        cuisine_type="boba",
                        google_maps_url=place_data.get("google_maps_url"),
                        photo_url=place_data.get("photo_url"),
                        is_open_now=place_data.get("is_open_now"),
                        lat=None,  # Could extract from geometry if needed
                        lng=None
                    )
                    db.add(restaurant)
                    db.commit()
                    db.refresh(restaurant)
                else:
                    # Update if needed
                    if restaurant.photo_url is None and place_data.get("photo_url"):
                        restaurant.photo_url = place_data.get("photo_url")
                    if restaurant.is_open_now is None:
                        restaurant.is_open_now = place_data.get("is_open_now")
                    db.commit()
                
                # Get check-in count
                check_in = db.query(CheckIn).filter(CheckIn.restaurant_id == restaurant.id).first()
                check_in_count = check_in.check_in_count if check_in else 0
                
                restaurants.append({
                    "id": restaurant.id,
                    "place_id": restaurant.place_id,
                    "name": restaurant.name or "Unknown",
                    "address": restaurant.address or "",
                    "phone": restaurant.phone,
                    "rating": restaurant.rating,
                    "user_ratings_total": restaurant.user_ratings_total,
                    "price_level": restaurant.price_level,
                    "google_maps_url": restaurant.google_maps_url,
                    "photo_url": restaurant.photo_url,
                    "is_open_now": restaurant.is_open_now,
                    "check_in_count": check_in_count,
                    "distance_miles": place_data.get("distance_miles")
                })
            
            print(f"[Food API] Returning {len(restaurants)} boba recommendations")
            return {"restaurants": restaurants}
            
        except Exception as e:
            print(f"[Food API] Error in boba service: {e}")
            import traceback
            traceback.print_exc()
            # Fall through to regular search as fallback
    
    # Map cuisine types to Google Places search terms
    cuisine_map = {
        "chinese": "Chinese restaurant",
        "japanese": "Japanese restaurant",
        "korean": "Korean restaurant",
        "vietnamese": "Vietnamese restaurant"
    }
    
    search_query = cuisine_map.get(cuisine_type, "restaurant")
    # Monta Vista High School coordinates: 37.3206, -122.0444
    monta_vista_lat = 37.3206
    monta_vista_lng = -122.0444
    location = f"{monta_vista_lat},{monta_vista_lng}"  # Monta Vista High School coordinates
    radius = 8047  # 5 miles = 8047 meters
    max_distance_miles = 5.0  # Maximum distance in miles
    
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in miles using Haversine formula"""
        R = 3959  # Earth radius in miles
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    try:
        # Search for places
        async with httpx.AsyncClient() as client:
            # First, search for places
            search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            # Use Monta Vista High School as reference point
            search_params = {
                "query": f"{search_query} near Monta Vista High School Cupertino CA",
                "key": GOOGLE_MAPS_API_KEY,
                "type": "restaurant",
                "location": location,
                "radius": radius
            }
            
            print(f"[Food API] Searching for {cuisine_type} restaurants with query: {search_query}")
            search_response = await client.get(search_url, params=search_params)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            print(f"[Food API] Google Places API response status: {search_data.get('status')}")
            print(f"[Food API] Found {len(search_data.get('results', []))} places")
            
            if search_data.get("status") != "OK":
                error_msg = f"Google Places API error: {search_data.get('status')}"
                if search_data.get("error_message"):
                    error_msg += f" - {search_data.get('error_message')}"
                print(f"[Food API] {error_msg}")
                
                # If API key has restrictions, return mock data instead of error
                if search_data.get("status") == "REQUEST_DENIED":
                    print("[Food API] API key has restrictions. Returning mock data.")
                    # Return mock data
                    mock_restaurants = []
                    cuisine_names = {
                        "chinese": ["川菜馆", "粤菜馆", "湘菜馆", "东北菜", "上海菜"],
                        "japanese": ["寿司店", "拉面馆", "日式烧烤", "居酒屋", "日式料理"],
                        "korean": ["韩式烧烤", "韩式料理", "韩国炸鸡", "韩式汤饭", "韩式火锅"],
                        "vietnamese": ["越南粉", "越式料理", "越南菜", "越式春卷", "越式河粉"],
                        "boba": ["奶茶店", "珍珠奶茶", "水果茶", "芝士茶", "波霸奶茶"]
                    }
                    names = cuisine_names.get(cuisine_type, ["示例餐厅"])
                    for i, name in enumerate(names[:5], 1):
                        mock_restaurants.append({
                            "id": i,
                            "place_id": f"mock_place_{cuisine_type}_{i}",
                            "name": f"{name} {i}",
                            "address": f"Cupertino, CA {i}",
                            "phone": None,
                            "rating": 4.0 + (i * 0.1),
                            "user_ratings_total": 50 + (i * 10),
                            "price_level": i % 4,
                            "google_maps_url": f"https://www.google.com/maps/place/example{i}",
                            "photo_url": None,
                            "is_open_now": i % 2 == 0,
                            "check_in_count": 0
                        })
                    return {"restaurants": mock_restaurants}
                
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Get results (boba is handled separately above)
            places = search_data.get("results", [])[:limit]
            print(f"[Food API] Processing {len(places)} places")
            
            restaurants = []
            for place in places:
                place_id = place.get("place_id")
                if not place_id:
                    continue
                
                # Check if restaurant exists in DB
                restaurant = db.query(Restaurant).filter(Restaurant.place_id == place_id).first()
                
                if not restaurant:
                    # Get place details
                    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                    details_params = {
                        "place_id": place_id,
                        "key": GOOGLE_MAPS_API_KEY,
                        "fields": "name,formatted_address,formatted_phone_number,rating,user_ratings_total,price_level,opening_hours,geometry,photos,url"
                    }
                    
                    details_response = await client.get(details_url, params=details_params)
                    details_response.raise_for_status()
                    details_data = details_response.json()
                    
                    if details_data.get("status") != "OK":
                        continue
                    
                    result = details_data.get("result", {})
                    
                    # Get photo URL if available
                    photo_url = None
                    if result.get("photos"):
                        photo_ref = result["photos"][0].get("photo_reference")
                        if photo_ref:
                            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={GOOGLE_MAPS_API_KEY}"
                    
                    # Check if open now
                    is_open_now = None
                    if result.get("opening_hours"):
                        is_open_now = result["opening_hours"].get("open_now")
                    
                    # Get coordinates
                    geometry = result.get("geometry", {})
                    place_location = geometry.get("location", {})
                    place_lat = place_location.get("lat")
                    place_lng = place_location.get("lng")
                    
                    # Calculate distance from Monta Vista High School and filter
                    if place_lat and place_lng:
                        distance_miles = calculate_distance(monta_vista_lat, monta_vista_lng, place_lat, place_lng)
                        if distance_miles > max_distance_miles:
                            print(f"[Food API] Skipping {result.get('name')} at {result.get('formatted_address')} - distance: {distance_miles:.2f} miles (beyond {max_distance_miles} miles)")
                            continue
                    
                    restaurant = Restaurant(
                        place_id=place_id,
                        name=result.get("name", ""),
                        address=result.get("formatted_address"),
                        phone=result.get("formatted_phone_number"),
                        rating=result.get("rating"),
                        user_ratings_total=result.get("user_ratings_total"),
                        price_level=result.get("price_level"),
                        cuisine_type=cuisine_type,
                        google_maps_url=result.get("url"),
                        photo_url=photo_url,
                        is_open_now=is_open_now,
                        lat=place_lat,
                        lng=place_lng
                    )
                    db.add(restaurant)
                    db.commit()
                    db.refresh(restaurant)
                else:
                    # Update opening hours if needed
                    if restaurant.is_open_now is None:
                        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                        details_params = {
                            "place_id": place_id,
                            "key": GOOGLE_MAPS_API_KEY,
                            "fields": "opening_hours"
                        }
                        
                        async with httpx.AsyncClient() as client2:
                            details_response = await client2.get(details_url, params=details_params)
                            if details_response.status_code == 200:
                                details_data = details_response.json()
                                if details_data.get("status") == "OK":
                                    result = details_data.get("result", {})
                                    if result.get("opening_hours"):
                                        restaurant.is_open_now = result["opening_hours"].get("open_now")
                                        db.commit()
                
                # Calculate distance from Monta Vista High School
                distance_miles = None
                if restaurant.lat and restaurant.lng:
                    distance_miles = calculate_distance(monta_vista_lat, monta_vista_lng, restaurant.lat, restaurant.lng)
                    # Filter out restaurants beyond 5 miles
                    if distance_miles > max_distance_miles:
                        print(f"[Food API] Skipping {restaurant.name} at {restaurant.address} - distance: {distance_miles:.2f} miles (beyond {max_distance_miles} miles)")
                        continue
                
                # Get check-in count
                check_in = db.query(CheckIn).filter(CheckIn.restaurant_id == restaurant.id).first()
                check_in_count = check_in.check_in_count if check_in else 0
                
                restaurants.append({
                    "id": restaurant.id,
                    "place_id": restaurant.place_id,
                    "name": restaurant.name or "Unknown",
                    "address": restaurant.address or "",
                    "phone": restaurant.phone,
                    "rating": restaurant.rating,
                    "user_ratings_total": restaurant.user_ratings_total,
                    "price_level": restaurant.price_level,
                    "google_maps_url": restaurant.google_maps_url,
                    "photo_url": restaurant.photo_url,
                    "is_open_now": restaurant.is_open_now,
                    "check_in_count": check_in_count,
                    "distance_miles": round(distance_miles, 2) if distance_miles else None
                })
            
            return {"restaurants": restaurants}
    
    except Exception as e:
        print(f"Error fetching restaurants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkin/{restaurant_id}")
async def check_in(
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    """
    Increment check-in count for a restaurant
    """
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Get or create check-in record
    check_in = db.query(CheckIn).filter(CheckIn.restaurant_id == restaurant_id).first()
    
    if check_in:
        check_in.check_in_count += 1
        check_in.last_check_in_at = datetime.now()
    else:
        check_in = CheckIn(
            restaurant_id=restaurant_id,
            check_in_count=1
        )
        db.add(check_in)
    
    db.commit()
    db.refresh(check_in)
    
    return {
        "restaurant_id": restaurant_id,
        "check_in_count": check_in.check_in_count,
        "last_check_in_at": check_in.last_check_in_at.isoformat()
    }


@router.get("/explore")
async def get_explore_posts(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get popular posts about new Chinese restaurants in Cupertino area from 1point3acres and huaren
    """
    # Helper function to check if article is about restaurants/food
    def is_food_related(article: Article) -> bool:
        """Check if article is about restaurants or food"""
        food_keywords = [
            "餐厅", "餐馆", "restaurant", "美食", "探店", "新店", "中餐", "日料", "韩餐",
            "火锅", "烧烤", "川菜", "粤菜", "湘菜", "鲁菜", "淮扬菜", "本帮菜",
            "dim sum", "点心", "奶茶", "boba", "tea", "cafe", "coffee",
            "food", "dining", "cuisine", "menu", "dish", "meal"
        ]
        
        full_text = f"{article.title or ''} {article.summary or ''} {article.cleaned_text or ''}".lower()
        return any(keyword in full_text for keyword in food_keywords)
    
    # Helper function to check if article is Bay Area related
    def is_bay_area_related(article: Article) -> bool:
        """Check if article mentions Bay Area cities or locations"""
        bay_area_cities = [
            "cupertino", "san jose", "santa clara", "sunnyvale", "mountain view",
            "palo alto", "fremont", "milpitas", "campbell", "los altos",
            "saratoga", "san francisco", "sf", "oakland", "berkeley",
            "foster city", "redwood city", "menlo park", "burlingame",
            "san mateo", "daly city", "south bay", "east bay", "peninsula"
        ]
        
        full_text = f"{article.title or ''} {article.summary or ''} {article.cleaned_text or ''}".lower()
        # Also check city_hints
        if article.city_hints:
            try:
                cities = json.loads(article.city_hints)
                if isinstance(cities, list):
                    for city in cities:
                        if any(bay_city in str(city).lower() for bay_city in bay_area_cities):
                            return True
            except:
                pass
        return any(bay_city in full_text for bay_city in bay_area_cities)
    
    # Helper function to check if article is popular
    def is_popular(article: Article) -> bool:
        """Check if article is popular based on engagement metrics"""
        # For huaren/1point3acres: consider popular if:
        # - views > 50 OR
        # - engagement_score > 5 OR
        # - final_score > 0.25
        return (article.views or 0) > 50 or (article.engagement_score or 0) > 5 or (article.final_score or 0) > 0.25
    
    # Search for articles from 1point3acres and huaren with food_radar source_type
    cutoff_time = datetime.now() - timedelta(days=30)  # Last 30 days
    
    base_query = db.query(Article).filter(
        or_(
            Article.url.ilike('%1point3acres.com%'),
            Article.url.ilike('%huaren.us%')
        ),
        Article.source_type == "food_radar",
        Article.published_at >= cutoff_time
    )
    
    # Get all articles and filter by Bay Area relevance and popularity
    articles = base_query.all()
    filtered_articles = []
    
    for article in articles:
        # Must be food-related AND Bay Area related AND popular
        if is_food_related(article) and is_bay_area_related(article) and is_popular(article):
            filtered_articles.append(article)
    
    # Sort by final_score (highest first)
    filtered_articles.sort(key=lambda a: a.final_score or 0, reverse=True)
    
    # Limit results
    filtered_articles = filtered_articles[:limit]
    
    result = []
    for article in filtered_articles:
        result.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "summary": article.summary,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "thumbnail_url": article.thumbnail_url
        })
    
    return {"posts": result}


@router.get("/bloggers")
async def get_food_blogger_videos(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get latest videos from popular Chinese food bloggers on YouTube
    Uses Google Custom Search to find the most popular food bloggers
    """
    from app.services.google_search import search_google, fetch_multiple_pages
    
    # Use Google Custom Search to find popular Chinese food blogger videos
    search_query = "中餐美食博主 site:youtube.com"
    
    try:
        # Fetch YouTube videos from Google search
        search_results = fetch_multiple_pages(
            query=search_query,
            site_domain="youtube.com",
            max_results=limit * 2,  # Fetch more to filter
            date_restrict="d7"  # Last 7 days
        )
        
        result = []
        seen_urls = set()
        
        for item in search_results:
            url = item.get("link", "")
            if not url or "youtube.com" not in url.lower():
                continue
            
            # Skip duplicates
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Extract video ID from URL
            video_id = None
            if "watch?v=" in url:
                video_id = url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            
            if not video_id:
                continue
            
            # Get thumbnail URL
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            result.append({
                "id": f"search_{len(result)}",  # Temporary ID
                "title": item.get("title", ""),
                "url": url,
                "summary": item.get("snippet", ""),
                "thumbnail_url": thumbnail_url,
                "video_id": video_id,
                "published_at": None  # Google CSE doesn't provide publish date
            })
            
            if len(result) >= limit:
                break
        
        # If we don't have enough results from search, fall back to database
        if len(result) < limit:
            cutoff_time = datetime.now() - timedelta(days=7)
            articles = db.query(Article).filter(
                Article.url.ilike('%youtube.com%'),
                Article.source_type == "food_radar",
                Article.published_at >= cutoff_time
            ).order_by(desc(Article.final_score)).limit(limit - len(result)).all()
            
            for article in articles:
                if article.url not in seen_urls:
                    result.append({
                        "id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "summary": article.summary,
                        "thumbnail_url": article.thumbnail_url,
                        "video_id": article.video_id,
                        "published_at": article.published_at.isoformat() if article.published_at else None
                    })
                    if len(result) >= limit:
                        break
        
        return {"videos": result[:limit]}
    
    except Exception as e:
        print(f"Error fetching food blogger videos from Google search: {e}")
        # Fall back to database query
        cutoff_time = datetime.now() - timedelta(days=7)
        articles = db.query(Article).filter(
            Article.url.ilike('%youtube.com%'),
            Article.source_type == "food_radar",
            Article.published_at >= cutoff_time
        ).order_by(desc(Article.final_score)).limit(limit).all()
        
        result = []
        for article in articles:
            result.append({
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "summary": article.summary,
                "thumbnail_url": article.thumbnail_url,
                "video_id": article.video_id,
                "published_at": article.published_at.isoformat() if article.published_at else None
            })
        
        return {"videos": result}


@router.get("/today-pick")
async def get_today_pick(
    city: str = Query(default="cupertino", description="City name (e.g., cupertino, sunnyvale)"),
    db: Session = Depends(get_db)
):
    """
    Get today's food pick (restaurant + recommended dish)
    
    Returns:
    - Randomly selected Chinese restaurant (deterministic per day)
    - Best dish from the restaurant (from reviews or fallback)
    - Google Maps URL for direct navigation
    
    Cached for 24 hours. Same result for all users on the same day.
    """
    from app.services.food_today_service import fetch_today_pick
    
    try:
        return fetch_today_pick(city=city, db=db)
    except Exception as e:
        print(f"Error in /food/today-pick: {e}")
        import traceback
        traceback.print_exc()
        # Never return 500, always return fallback
        from datetime import datetime
        import pytz
        today = datetime.now(pytz.UTC)
        date_str = today.strftime("%Y-%m-%d")
        from app.services.food_today_service import get_mock_today_pick
        return get_mock_today_pick(city, date_str)

