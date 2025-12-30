"""
Entertainment endpoints for YouTube videos (TV shows / Variety shows)
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict
import os
import httpx
import redis
from datetime import datetime
import json

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Entertainment channels (TV shows / Variety shows)
ENTERTAINMENT_CHANNELS = [
    "Tencent Video - Get the WeTV APP",
    "iQIYI 爱奇艺 - Get the iQIYI APP",
    "YOUKU-Get APP now"
]

# Mock data for fallback
MOCK_YOUTUBE_VIDEOS = [
    {
        "videoId": "dQw4w9WgXcQ",
        "title": "最新电视剧推荐 2024",
        "title_cn": "最新电视剧推荐 2024",
        "thumbnail": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "channelTitle": "Tencent Video - Get the WeTV APP",
        "type": "tv"
    },
    {
        "videoId": "jNQXAC9IVRw",
        "title": "最新综艺节目 2024",
        "title_cn": "最新综艺节目 2024",
        "thumbnail": "https://img.youtube.com/vi/jNQXAC9IVRw/mqdefault.jpg",
        "channelTitle": "iQIYI 爱奇艺 - Get the iQIYI APP",
        "type": "variety"
    }
]


def get_cache_key(channel_list: List[str], video_type: str) -> str:
    """Generate cache key for YouTube channel search"""
    today = datetime.now().strftime("%Y%m%d")
    channels_str = "_".join(sorted(channel_list))
    return f"entertainment:youtube:{video_type}:{channels_str}:{today}"


def search_channel_videos(
    channel_name: str,
    max_results: int = 2
) -> List[Dict]:
    """
    Search YouTube channel videos using Google Custom Search API
    Returns list of video items with videoId, title, thumbnail, channelTitle
    Focuses on getting latest videos from the specific channel by searching channel's uploads page
    """
    from app.services.google_search import fetch_multiple_pages, search_google
    
    try:
        # Strategy: Search for channel's uploads/videos page to get latest videos (last 3 days)
        # Use multiple query formats to find the channel's latest uploads
        # Extract channel handle/name for search
        channel_search_name = channel_name
        # Try to extract handle if it's in parentheses or after dash
        if "(" in channel_name:
            # Extract text before parentheses as search term
            channel_search_name = channel_name.split("(")[0].strip()
        elif "-" in channel_name:
            # Use part before dash
            channel_search_name = channel_name.split("-")[0].strip()
        
        search_queries = [
            # Search for popular/trending videos from channel (last 3 days)
            f'"{channel_name}" popular trending site:youtube.com',
            # Channel search name with hot videos
            f'"{channel_search_name}" hot videos site:youtube.com',
            # Channel name with most viewed (last 3 days)
            f'"{channel_name}" most viewed site:youtube.com',
            # Channel search name with trending
            f'"{channel_search_name}" trending site:youtube.com'
        ]
        
        all_results = []
        for search_query in search_queries:
            try:
                # Use single page search first (faster, more recent results)
                search_result = search_google(
                    query=search_query,
                    site_domain="youtube.com",
                    num=10,  # Get top 10 results
                    date_restrict="d3"  # Last 3 days ONLY - strict requirement
                )
                
                # Google CSE results are typically sorted by relevance/popularity
                # which should give us the "hottest" videos
                
                if search_result.get("items"):
                    all_results.extend(search_result["items"])
                
                # If we have enough results, break
                if len(all_results) >= max_results * 3:
                    break
            except Exception as e:
                print(f"Error with query '{search_query}': {e}")
                continue
        
        videos = []
        seen_video_ids = set()
        
        for item in all_results:
            url = item.get("link", "")
            if not url:
                continue
            
            # Only accept watch URLs (actual videos, not channel pages or playlists)
            if "/watch" not in url.lower() and "youtu.be/" not in url.lower():
                continue
            
            # Skip playlist URLs
            if "/playlist" in url.lower():
                continue
            
            # Extract video ID from URL
            video_id = None
            if "watch?v=" in url:
                video_id = url.split("watch?v=")[1].split("&")[0].split("#")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0].split("#")[0]
            
            if not video_id or len(video_id) != 11 or video_id in seen_video_ids:
                continue
            seen_video_ids.add(video_id)
            
            # Verify this is from the correct channel by checking snippet/displayLink
            snippet = item.get("snippet", "").lower()
            display_link = item.get("displayLink", "").lower()
            title = item.get("title", "").lower()
            channel_lower = channel_name.lower()
            search_name_lower = channel_search_name.lower()
            
            # Check if result is related to our channel (use both full name and search name)
            channel_match = (
                channel_lower in snippet or
                channel_lower in display_link or
                channel_lower in title or
                search_name_lower in snippet or
                search_name_lower in display_link or
                search_name_lower in title
            )
            
            # Additional checks for specific channel patterns
            if "tencent" in channel_lower or "wetv" in channel_lower:
                channel_match = channel_match or "tencent" in snippet or "wetv" in snippet or "wetv" in display_link
            if "iqiyi" in channel_lower or "爱奇艺" in channel_name:
                channel_match = channel_match or "iqiyi" in snippet or "爱奇艺" in snippet or "iqiyi" in display_link
            if "youku" in channel_lower:
                channel_match = channel_match or "youku" in snippet or "youku" in display_link
            
            # If we can't verify channel match, still include it but with lower priority
            # (we'll filter later if needed)
            
            # Get thumbnail URL (medium quality)
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            
            videos.append({
                "videoId": video_id,
                "title": item.get("title", ""),
                "title_cn": item.get("title", ""),
                "thumbnail": thumbnail_url,
                "channelTitle": channel_name,
                "url": url,
                "channel_match": channel_match,  # Flag for filtering
                "snippet": snippet  # For debugging
            })
            
            if len(videos) >= max_results * 2:
                break
        
        # Prioritize videos that match the channel
        matched_videos = [v for v in videos if v.get("channel_match", False)]
        other_videos = [v for v in videos if not v.get("channel_match", False)]
        
        # Google CSE results are already sorted by relevance/popularity (hottest first)
        # So we keep the original order which represents "hottest" videos
        # Combine: matched first (already sorted by popularity), then others
        sorted_videos = matched_videos + other_videos
        
        # Note: Google CSE sorts by relevance which typically correlates with:
        # - View count
        # - Engagement (likes, comments)
        # - Recency within the date range
        # This gives us the "hottest" videos from the last 3 days
        
        # Remove channel_match and snippet from final output
        final_videos = []
        for video in sorted_videos[:max_results]:
            final_video = {k: v for k, v in video.items() if k not in ["channel_match", "snippet"]}
            final_videos.append(final_video)
        
        return final_videos
    except Exception as e:
        print(f"Error searching channel videos for {channel_name}: {e}")
        import traceback
        traceback.print_exc()
        return []


@router.get("/youtube")
async def get_youtube_entertainment(
    type: str = Query(default="tv", description="Type: tv (电视剧) or variety (综艺)"),
    limit: int = Query(default=12, ge=1, le=20),
    channels: Optional[str] = Query(None, description="Comma-separated channel names (default: predefined entertainment channels)")
):
    """
    Get YouTube entertainment videos (TV shows / Variety shows)
    Fetches latest videos from specified entertainment channels
    """
    # Use provided channels or default entertainment channels
    channel_list = [ch.strip() for ch in channels.split(",")] if channels else ENTERTAINMENT_CHANNELS
    
    # Calculate videos per channel (get at least 2 per channel to have options)
    videos_per_channel = max(2, (limit // len(channel_list)) + 1)
    
    # Check cache first (reduce cache time to 2 hours for fresher content)
    cache_key = get_cache_key(channel_list, type)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                cached_data = json.loads(cached)
                # Check if cache is too old (more than 2 hours)
                cached_at = cached_data.get("cached_at")
                if cached_at:
                    try:
                        from dateutil import parser
                        cache_time = parser.parse(cached_at)
                        age_hours = (datetime.now() - cache_time.replace(tzinfo=None)).total_seconds() / 3600
                        if age_hours < 2:  # Use cache if less than 2 hours old
                            return cached_data
                    except:
                        pass
            except:
                pass
    
    try:
        all_videos = []
        
        # Fetch from each channel
        for channel in channel_list:
            videos = search_channel_videos(channel.strip(), max_results=videos_per_channel)
            all_videos.extend(videos)
        
        # Remove duplicates by videoId and sort by recency (most recent first)
        seen = set()
        unique_videos = []
        for video in all_videos:
            if video["videoId"] not in seen:
                seen.add(video["videoId"])
                unique_videos.append(video)
        
        # Sort by channel order (maintain channel diversity) and limit
        # Try to get at least 1 video from each channel if possible
        channel_video_map = {}
        for video in unique_videos:
            channel = video.get("channelTitle", "")
            if channel not in channel_video_map:
                channel_video_map[channel] = []
            channel_video_map[channel].append(video)
        
        # Interleave videos from different channels to maintain diversity
        final_videos = []
        max_per_channel = max(1, limit // len(channel_list))
        channel_indices = {ch: 0 for ch in channel_list}
        
        while len(final_videos) < limit:
            added = False
            for channel in channel_list:
                if channel in channel_video_map and channel_indices[channel] < len(channel_video_map[channel]) and channel_indices[channel] < max_per_channel:
                    video = channel_video_map[channel][channel_indices[channel]]
                    if video["videoId"] not in [v["videoId"] for v in final_videos]:
                        final_videos.append(video)
                        added = True
                    channel_indices[channel] += 1
                    if len(final_videos) >= limit:
                        break
            if not added:
                # If no more videos from preferred channels, add remaining
                for video in unique_videos:
                    if video["videoId"] not in [v["videoId"] for v in final_videos]:
                        final_videos.append(video)
                        if len(final_videos) >= limit:
                            break
                break
        
        unique_videos = final_videos[:limit]
        
        # If we have results, cache them (reduce to 2 hours for fresher content)
        if unique_videos and redis_client:
            # Cache for 2 hours to get fresher videos
            redis_client.setex(cache_key, 2 * 3600, json.dumps({
                "items": unique_videos,
                "type": type,
                "channels": channel_list,
                "total": len(unique_videos),
                "cached_at": datetime.now().isoformat(),
                "dataSource": "youtube"
            }))
        
        if unique_videos:
            return {
                "items": unique_videos,
                "type": type,
                "channels": channel_list,
                "total": len(unique_videos),
                "dataSource": "youtube"
            }
    except Exception as e:
        print(f"Error fetching YouTube entertainment: {e}")
    
    # Fallback to mock data
    mock_items = [v for v in MOCK_YOUTUBE_VIDEOS if v.get("type") == type or type not in ["tv", "variety"]]
    return {
        "items": mock_items[:limit],
        "type": type,
        "channels": channel_list,
        "total": len(mock_items),
        "dataSource": "mock"
    }

