"""
YouTube Channels endpoint for fetching videos from multiple channels
Supports stock analysis and tech channels
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Optional
import os
import redis
from datetime import datetime
import json

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Stock analysis channels
STOCK_CHANNELS = [
    "视野环球财经",
    "美投讲美股",
    "美投侃新闻",
    "股市咖啡屋 Stock Cafe",
    "老李玩钱"
]

# Tech channels
TECH_CHANNELS = [
    "硅谷101",
    "最强拍档"
]

# Mock data for fallback
MOCK_STOCK_VIDEOS = [
    {
        "videoId": "dQw4w9WgXcQ",
        "title": "美股最新分析：科技股走势",
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "duration": "15:30",
        "channelTitle": "视野环球财经",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
]

MOCK_TECH_VIDEOS = [
    {
        "videoId": "jNQXAC9IVRw",
        "title": "硅谷最新动态：AI 芯片竞争",
        "thumbnail": "https://img.youtube.com/vi/jNQXAC9IVRw/mqdefault.jpg",
        "duration": "20:15",
        "channelTitle": "硅谷101",
        "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    }
]


def get_cache_key(channel_list: List[str], category: str) -> str:
    """Generate cache key for multiple channels"""
    today = datetime.now().strftime("%Y%m%d")
    channels_str = "_".join(sorted(channel_list))
    return f"youtube:channels:{category}:{channels_str}:{today}"


def search_channel_videos(
    channel_name: str,
    max_results: int = 1
) -> List[Dict]:
    """
    Search YouTube channel videos using Google Custom Search API
    Returns list of video items with videoId, title, thumbnail, duration
    """
    from app.services.google_search import fetch_multiple_pages
    
    try:
        # Search for videos from specific channel
        search_query = f'"{channel_name}" site:youtube.com'
        
        search_results = fetch_multiple_pages(
            query=search_query,
            site_domain="youtube.com",
            max_results=max_results * 3,  # Fetch more to filter
            date_restrict="d7"  # Last 7 days
        )
        
        videos = []
        seen_video_ids = set()
        
        for item in search_results:
            url = item.get("link", "")
            if not url or ("youtube.com" not in url.lower() and "youtu.be" not in url.lower()):
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
            
            # Get thumbnail URL
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            
            # Extract duration from snippet (if available) - Google CSE doesn't provide this
            # We'll use a placeholder or try to extract from title
            duration = "N/A"  # Will be fetched separately if needed
            
            videos.append({
                "videoId": video_id,
                "title": item.get("title", ""),
                "thumbnail": thumbnail_url,
                "duration": duration,
                "channelTitle": channel_name,
                "url": url
            })
            
            if len(videos) >= max_results:
                break
        
        return videos
    except Exception as e:
        print(f"Error searching channel videos for {channel_name}: {e}")
        return []


@router.get("/stock")
async def get_stock_analysis_videos(
    channels: Optional[str] = Query(None, description="Comma-separated channel names"),
    limit_per_channel: int = Query(1, ge=1, le=3, description="Videos per channel")
):
    """
    Get latest videos from stock analysis channels
    Each channel returns latest 1 video by default
    """
    channel_list = channels.split(",") if channels else STOCK_CHANNELS
    
    # Check cache first
    cache_key = get_cache_key(channel_list, "stock")
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    try:
        all_videos = []
        
        # Fetch from each channel
        for channel in channel_list:
            videos = search_channel_videos(channel.strip(), max_results=limit_per_channel)
            all_videos.extend(videos)
        
        # If we have results, cache them
        if all_videos and redis_client:
            # Cache for 6 hours
            redis_client.setex(cache_key, 6 * 3600, json.dumps({
                "items": all_videos,
                "channels": channel_list,
                "total": len(all_videos),
                "cached_at": datetime.now().isoformat(),
                "dataSource": "youtube"
            }))
        
        if all_videos:
            return {
                "items": all_videos,
                "channels": channel_list,
                "total": len(all_videos),
                "dataSource": "youtube"
            }
    except Exception as e:
        print(f"Error fetching stock analysis videos: {e}")
    
    # Fallback to mock data
    return {
        "items": MOCK_STOCK_VIDEOS,
        "channels": channel_list,
        "total": len(MOCK_STOCK_VIDEOS),
        "dataSource": "mock"
    }


@router.get("/tech")
async def get_tech_videos(
    channels: Optional[str] = Query(None, description="Comma-separated channel names"),
    limit_per_channel: int = Query(3, ge=1, le=5, description="Videos per channel")
):
    """
    Get latest videos from tech channels
    Each channel returns latest 3 videos by default
    """
    channel_list = channels.split(",") if channels else TECH_CHANNELS
    
    # Check cache first
    cache_key = get_cache_key(channel_list, "tech")
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    try:
        all_videos = []
        
        # Fetch from each channel
        for channel in channel_list:
            videos = search_channel_videos(channel.strip(), max_results=limit_per_channel)
            all_videos.extend(videos)
        
        # Sort by recency (most recent first) - approximate based on search order
        # Remove duplicates
        seen = set()
        unique_videos = []
        for video in all_videos:
            if video["videoId"] not in seen:
                seen.add(video["videoId"])
                unique_videos.append(video)
        
        # If we have results, cache them
        if unique_videos and redis_client:
            # Cache for 6 hours
            redis_client.setex(cache_key, 6 * 3600, json.dumps({
                "items": unique_videos,
                "channels": channel_list,
                "total": len(unique_videos),
                "cached_at": datetime.now().isoformat(),
                "dataSource": "youtube"
            }))
        
        if unique_videos:
            return {
                "items": unique_videos,
                "channels": channel_list,
                "total": len(unique_videos),
                "dataSource": "youtube"
            }
    except Exception as e:
        print(f"Error fetching tech videos: {e}")
    
    # Fallback to mock data
    return {
        "items": MOCK_TECH_VIDEOS,
        "channels": channel_list,
        "total": len(MOCK_TECH_VIDEOS),
        "dataSource": "mock"
    }

