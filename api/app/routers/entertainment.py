"""
Entertainment endpoints for YouTube videos (TV shows / Variety shows)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict
import os
import httpx
import redis
from datetime import datetime

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Mock data for fallback
MOCK_YOUTUBE_VIDEOS = [
    {
        "videoId": "dQw4w9WgXcQ",
        "title": "最新电视剧推荐 2024",
        "title_cn": "最新电视剧推荐 2024",
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "channelTitle": "电视剧频道",
        "type": "tv"
    },
    {
        "videoId": "jNQXAC9IVRw",
        "title": "最新综艺节目 2024",
        "title_cn": "最新综艺节目 2024",
        "thumbnail": "https://img.youtube.com/vi/jNQXAC9IVRw/mqdefault.jpg",
        "channelTitle": "综艺频道",
        "type": "variety"
    }
]


def get_cache_key(query: str, video_type: str) -> str:
    """Generate cache key for YouTube search"""
    today = datetime.now().strftime("%Y%m%d")
    return f"entertainment:youtube:{video_type}:{today}"


def search_youtube_videos(
    query: str,
    max_results: int = 8
) -> List[Dict]:
    """
    Search YouTube videos using Google Custom Search API
    Returns list of video items with videoId, title, thumbnail, channelTitle
    """
    from app.services.google_search import fetch_multiple_pages
    
    try:
        # Search YouTube with the query
        search_results = fetch_multiple_pages(
            query=f"{query} site:youtube.com",
            site_domain="youtube.com",
            max_results=max_results * 2,  # Fetch more to filter
            date_restrict="d7"  # Last 7 days
        )
        
        videos = []
        seen_video_ids = set()
        
        for item in search_results:
            url = item.get("link", "")
            if not url or "youtube.com" not in url.lower() and "youtu.be" not in url.lower():
                continue
            
            # Extract video ID from URL
            video_id = None
            if "watch?v=" in url:
                video_id = url.split("watch?v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            
            if not video_id or video_id in seen_video_ids:
                continue
            seen_video_ids.add(video_id)
            
            # Get thumbnail URL (medium quality)
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            
            # Extract channel name from displayLink or snippet
            channel_title = "YouTube"
            display_link = item.get("displayLink", "")
            if display_link and "youtube.com" in display_link:
                # Try to extract channel name from URL
                if "/channel/" in url or "/user/" in url or "/c/" in url:
                    # Channel page, use displayLink
                    channel_title = display_link.replace("www.youtube.com", "").replace("youtube.com", "").strip("/")
                else:
                    channel_title = "YouTube"
            
            videos.append({
                "videoId": video_id,
                "title": item.get("title", ""),
                "title_cn": item.get("title", ""),  # Will be translated by Gemini if needed
                "thumbnail": thumbnail_url,
                "channelTitle": channel_title,
                "url": url
            })
            
            if len(videos) >= max_results:
                break
        
        return videos
    except Exception as e:
        print(f"Error searching YouTube videos: {e}")
        return []


@router.get("/youtube")
async def get_youtube_entertainment(
    type: str = Query(default="tv", description="Type: tv (电视剧) or variety (综艺)"),
    limit: int = Query(default=12, ge=1, le=20)
):
    """
    Get YouTube entertainment videos (TV shows / Variety shows)
    Uses Google Custom Search to find latest videos
    """
    # Determine search query based on type
    if type == "tv":
        search_query = "最新电视剧"
    elif type == "variety":
        search_query = "最新综艺"
    else:
        search_query = "最新电视剧 最新综艺"
    
    # Check cache first
    cache_key = get_cache_key(search_query, type)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                import json
                return json.loads(cached)
            except:
                pass
    
    try:
        # Search for videos (synchronous function)
        videos = search_youtube_videos(search_query, max_results=limit)
        
        # If we have results, cache them
        if videos and redis_client:
            import json
            # Cache for 12 hours
            redis_client.setex(cache_key, 12 * 3600, json.dumps({
                "items": videos,
                "type": type,
                "total": len(videos),
                "cached_at": datetime.now().isoformat()
            }))
        
        if videos:
            return {
                "items": videos,
                "type": type,
                "total": len(videos),
                "dataSource": "youtube"
            }
    except Exception as e:
        print(f"Error fetching YouTube entertainment: {e}")
    
    # Fallback to mock data
    mock_items = [v for v in MOCK_YOUTUBE_VIDEOS if v.get("type") == type or type not in ["tv", "variety"]]
    return {
        "items": mock_items[:limit],
        "type": type,
        "total": len(mock_items),
        "dataSource": "mock"
    }

