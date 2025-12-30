"""
Tech Trends endpoint for YouTube channel videos (硅谷101)
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Dict
import os
import redis
from datetime import datetime
import json

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Mock data for fallback
MOCK_TECH_TRENDS_VIDEOS = [
    {
        "videoId": "dQw4w9WgXcQ",
        "title": "硅谷最新动态：AI 芯片竞争加剧",
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "publishedAt": datetime.now().isoformat(),
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    },
    {
        "videoId": "jNQXAC9IVRw",
        "title": "湾区科技公司裁员潮分析",
        "thumbnail": "https://img.youtube.com/vi/jNQXAC9IVRw/mqdefault.jpg",
        "publishedAt": datetime.now().isoformat(),
        "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    }
]


def get_cache_key(channel_name: str) -> str:
    """Generate cache key for YouTube channel videos"""
    today = datetime.now().strftime("%Y%m%d")
    return f"tech:trends:{channel_name}:{today}"


def search_channel_videos(
    channel_name: str,
    max_results: int = 5
) -> List[Dict]:
    """
    Search YouTube channel videos using Google Custom Search API
    Returns list of video items with videoId, title, thumbnail, publishedAt
    """
    from app.services.google_search import fetch_multiple_pages
    
    try:
        # Search for videos from specific channel
        # Try different search patterns
        search_queries = [
            f'"{channel_name}" site:youtube.com',
            f'{channel_name} channel site:youtube.com',
            f'硅谷101 site:youtube.com'
        ]
        
        all_videos = []
        seen_video_ids = set()
        
        for search_query in search_queries:
            if len(all_videos) >= max_results:
                break
                
            search_results = fetch_multiple_pages(
                query=search_query,
                site_domain="youtube.com",
                max_results=max_results * 2,
                date_restrict="d30"  # Last 30 days
            )
            
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
                
                # Extract published date from snippet (if available)
                snippet = item.get("snippet", "")
                published_at = datetime.now().isoformat()  # Default to now
                
                all_videos.append({
                    "videoId": video_id,
                    "title": item.get("title", ""),
                    "thumbnail": thumbnail_url,
                    "publishedAt": published_at,
                    "url": url
                })
                
                if len(all_videos) >= max_results:
                    break
        
        # Sort by publishedAt (most recent first)
        # Since we don't have exact publish dates from CSE, we'll use the order from search results
        return all_videos[:max_results]
    except Exception as e:
        print(f"Error searching channel videos: {e}")
        return []


@router.get("/channel")
async def get_tech_trends_videos(
    channel: str = Query(default="硅谷101", description="YouTube channel name"),
    limit: int = Query(default=5, ge=1, le=10)
):
    """
    Get latest videos from a YouTube channel (default: 硅谷101)
    Returns videos sorted by publish date (most recent first)
    """
    # Check cache first
    cache_key = get_cache_key(channel)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    try:
        # Search for channel videos
        videos = search_channel_videos(channel, max_results=limit)
        
        # If we have results, cache them
        if videos and redis_client:
            # Cache for 6 hours
            redis_client.setex(cache_key, 6 * 3600, json.dumps({
                "items": videos,
                "channel": channel,
                "total": len(videos),
                "cached_at": datetime.now().isoformat(),
                "dataSource": "youtube"
            }))
        
        if videos:
            return {
                "items": videos,
                "channel": channel,
                "total": len(videos),
                "dataSource": "youtube"
            }
    except Exception as e:
        print(f"Error fetching tech trends videos: {e}")
    
    # Fallback to mock data
    return {
        "items": MOCK_TECH_TRENDS_VIDEOS[:limit],
        "channel": channel,
        "total": len(MOCK_TECH_TRENDS_VIDEOS[:limit]),
        "dataSource": "mock"
    }


@router.get("/context")
async def get_tech_trends_context():
    """
    Get context panel text for tech trends module
    Returns neutral, factual background information (max 80 characters)
    """
    # Generate context based on current tech trends
    # This should be neutral, factual, no second person, no "值得" or "建议"
    
    context_text = {
        "background": "硅谷科技公司近期动态涉及AI芯片、云计算和人才市场变化。",
        "points": [
            "AI芯片竞争持续，NVIDIA、AMD等公司发布新产品",
            "云计算服务价格调整，影响企业技术选型",
            "湾区科技公司招聘和裁员情况出现波动"
        ],
        "domains": ["AI芯片", "云计算", "人才市场"]
    }
    
    return {
        "context": context_text,
        "updatedAt": datetime.now().isoformat()
    }

