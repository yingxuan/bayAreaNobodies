"""
Industry News Service for Bay Area Tech Workers
Aggregates, filters, scores, and summarizes tech news from multiple sources
"""
import os
import redis
import json
from typing import List, Dict
from datetime import datetime, timedelta
import pytz

from app.services.rss_fetcher import fetch_all_rss_feeds
from app.services.tech_trending_service import fetch_hn_stories
from app.services.news_blacklist import should_blacklist, is_big_tech_related
from app.services.news_relevance_scorer import score_news_item, rank_news_items
from app.services.news_summarizer import get_or_generate_summary
from app.services.news_judgment_service import get_cached_or_judge_batch, prefilter_blacklist

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 10 minutes for curated list
CURATED_CACHE_TTL = 600


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication"""
    from urllib.parse import urlparse
    if not url:
        return ""
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return normalized.lower()


def deduplicate_items(items: List[Dict]) -> List[Dict]:
    """Deduplicate by URL and title similarity"""
    seen_urls = set()
    seen_titles = set()
    deduplicated = []
    
    for item in items:
        url = normalize_url(item.get("url", ""))
        title = item.get("title", "").lower().strip()
        
        # Check URL
        if url and url in seen_urls:
            continue
        
        # Check title similarity (simple: exact match)
        if title and title in seen_titles:
            continue
        
        seen_urls.add(url)
        seen_titles.add(title)
        deduplicated.append(item)
    
    return deduplicated


def filter_and_score_items(raw_items: List[Dict], min_score: int = 30) -> List[Dict]:
    """
    Filter items by relevance and score them
    Returns scored and ranked items
    """
    filtered = []
    
    for item in raw_items:
        # Hard filter: blacklist check
        if should_blacklist(
            item.get("title", ""),
            item.get("description", ""),
            item.get("source", "")
        ):
            continue
        
        # Must be big tech related
        if not is_big_tech_related(item.get("title", ""), item.get("description", "")):
            continue
        
        # Score the item
        scored = score_news_item(item)
        
        # Filter by minimum score
        if scored.get("score", 0) >= min_score:
            filtered.append(scored)
    
    # Rank by score
    ranked = rank_news_items(filtered)
    
    return ranked


def aggregate_industry_news(target_count: int = 5, min_count: int = 4) -> List[Dict]:
    """
    Main aggregation function
    Returns 4-6 curated news items (target=5, min=4)
    """
    cache_key = f"industry_news:{datetime.now(pytz.UTC).strftime('%Y%m%d%H%M')}"  # 10 min cache
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                cached_items = json.loads(cached)
                # Convert ISO strings back to datetime
                for item in cached_items:
                    if isinstance(item.get("published_at"), str):
                        try:
                            from dateutil import parser
                            item["published_at"] = parser.parse(item["published_at"])
                        except:
                            item["published_at"] = datetime.now(pytz.UTC)
                
                if len(cached_items) >= min_count:
                    return cached_items[:target_count]
            except:
                pass
    
    # Collect from all sources
    all_raw_items = []
    
    # 1. RSS feeds
    try:
        rss_items = fetch_all_rss_feeds(limit_per_source=20)
        all_raw_items.extend(rss_items)
    except Exception as e:
        print(f"Error fetching RSS feeds: {e}")
    
    # 2. Hacker News (filtered for big tech)
    try:
        hn_stories = fetch_hn_stories(limit=30)
        for story in hn_stories:
            title = story.get("title", "")
            url = story.get("url", "")
            
            # Only include if big tech related
            if is_big_tech_related(title):
                # Parse published_at from story (HN uses "createdAt" as ISO string)
                published_at = datetime.now(pytz.UTC)
                created_at = story.get("createdAt") or story.get("created_at")
                if created_at:
                    try:
                        if isinstance(created_at, str):
                            from dateutil import parser
                            published_at = parser.parse(created_at)
                        else:
                            published_at = created_at
                        if published_at.tzinfo is None:
                            published_at = pytz.UTC.localize(published_at)
                    except:
                        pass
                
                all_raw_items.append({
                    "title": title,
                    "url": url,
                    "description": story.get("summary", ""),
                    "published_at": published_at,
                    "source": "Hacker News",
                    "source_key": "hn",
                })
    except Exception as e:
        print(f"Error fetching HN stories: {e}")
    
    # Deduplicate
    deduplicated = deduplicate_items(all_raw_items)
    
    # Filter and score (start with min_score=30) - basic relevance filtering
    scored_items = filter_and_score_items(deduplicated, min_score=30)
    
    # If not enough items, relax filter
    if len(scored_items) < min_count:
        scored_items = filter_and_score_items(deduplicated, min_score=20)
    
    # NEW STEP: ONE-CALL Gemini batch judgment pipeline
    # 1. Pre-filter hard blacklist keywords (EN + ZH)
    # 2. Take top 30-60 candidates
    # 3. Call Gemini ONCE for batch judgment (or get from cache)
    # 4. Returns dict with items[] (max 5), overall_brief_zh, etc.
    
    print(f"Pre-filtering {len(scored_items)} scored items with hard blacklist...")
    prefiltered = prefilter_blacklist(scored_items)
    print(f"After pre-filtering: {len(prefiltered)} items")
    
    # Take top 30 candidates for Gemini batch processing
    candidates = prefiltered[:30]
    
    # Call Gemini ONCE for batch judgment (or get from cache)
    # Returns dict with schema: {date_local, timezone, overall_brief_zh, shortage_reason, items[]}
    judged_result = get_cached_or_judge_batch(candidates)
    
    # Extract items from judged result
    judged_items = judged_result.get("items", [])
    
    # Take top items (already limited to 5 by Gemini)
    selected = judged_items[:target_count]
    
    # Store overall_brief_zh and other metadata in each item for API response
    # Also ensure all required fields are present
    for item in selected:
        item["overall_brief_zh"] = judged_result.get("overall_brief_zh", "")
        item["judged"] = True  # Flag to indicate this came from judgment pipeline
        # Ensure fields from Gemini are preserved
        if "id" not in item:
            item["id"] = item.get("url", "") or str(hash(item.get("title", "")))
        if "source_name" not in item:
            item["source_name"] = item.get("source", "Unknown")
    
    # If we have fewer than min_count after Gemini filtering, that's okay
    # We'll return what we have (frontend will show empty state if < 3)
    
    return selected


def format_industry_news_item(item: Dict) -> Dict:
    """Format item for API response"""
    from app.services.ai_news_service import parse_time_ago
    from datetime import datetime
    
    published_at = item.get("published_at")
    if isinstance(published_at, str):
        from dateutil import parser
        published_at = parser.parse(published_at)
    
    return {
        "title": item.get("original_title") or item.get("title", ""),  # Original English title (optional)
        "summary_zh": item.get("summary_zh", ""),
        "why_it_matters_zh": item.get("why_it_matters_zh", ""),
        "tags": item.get("tags", []),
        "original_url": item.get("url", ""),
        "source": item.get("source_name") or item.get("source", "Unknown"),
        "time_ago": parse_time_ago(published_at) if published_at else "",
        "published_at": published_at.isoformat() if published_at else None,
        "score": item.get("relevance_score", item.get("score", 0)),  # Use relevance_score from Gemini
        "reason": item.get("reason", ""),  # Why this item was selected
        "judged": item.get("judged", False),  # Flag indicating judgment pipeline
    }
