"""
Huaren.us Forum Service (Generic)
Fetches and parses threads from any Huaren.us forum
Supports forumid=395 (羊毛), forumid=398 (吃瓜), etc.
"""
import os
import json
import redis
import hashlib
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
import pytz

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 10 minutes (configurable)
CACHE_TTL = 600

# Rate limiting: at most 1 request per 30 seconds per server instance
RATE_LIMIT_SECONDS = 30
_last_request_time = 0

# Base URL
HUAREN_BASE_URL = "https://huaren.us"

# User agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_cache_key(forumid: int, page: int = 1) -> str:
    """Get Redis cache key for Huaren forum"""
    return f"huaren:forum{forumid}:page{page}"


def get_rate_limit_key() -> str:
    """Get rate limit key"""
    return "huaren:ratelimit"


def check_rate_limit() -> bool:
    """Check if we can make a request (rate limit)"""
    global _last_request_time
    
    if redis_client:
        rate_key = get_rate_limit_key()
        last_time = redis_client.get(rate_key)
        if last_time:
            try:
                last_time_float = float(last_time)
                elapsed = time.time() - last_time_float
                if elapsed < RATE_LIMIT_SECONDS:
                    return False  # Rate limited
            except:
                pass
    
    # Update rate limit
    current_time = time.time()
    _last_request_time = current_time
    if redis_client:
        redis_client.setex(get_rate_limit_key(), RATE_LIMIT_SECONDS, str(current_time))
    
    return True


def generate_thread_id(url: str, title: str) -> str:
    """Generate stable ID from URL and title"""
    # Try to extract thread ID from URL
    thread_id_match = re.search(r'threadid=(\d+)', url)
    if thread_id_match:
        return f"huaren-{thread_id_match.group(1)}"
    
    # Fallback: hash of normalized title + url
    normalized_title = title.strip().lower()
    normalized_url = url.lower().split('?')[0].split('#')[0]
    combined = f"{normalized_title}|{normalized_url}"
    hash_obj = hashlib.md5(combined.encode('utf-8'))
    return f"huaren-{hash_obj.hexdigest()[:12]}"


def extract_reply_count(text: str) -> Optional[int]:
    """Extract reply count from text like '回复: 123' or '123 回复'"""
    if not text:
        return None
    
    # Try patterns like "回复: 123", "123 回复", "回复 123"
    patterns = [
        r'回复[：:]\s*(\d+)',
        r'(\d+)\s*回复',
        r'回复\s*(\d+)',
        r'Replies?[：:]\s*(\d+)',
        r'(\d+)\s*replies?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    
    return None


def extract_view_count(text: str) -> Optional[int]:
    """Extract view count from text like '查看: 456' or '456 查看'"""
    if not text:
        return None
    
    # Try patterns like "查看: 456", "456 查看", "查看 456"
    patterns = [
        r'查看[：:]\s*(\d+)',
        r'(\d+)\s*查看',
        r'查看\s*(\d+)',
        r'Views?[：:]\s*(\d+)',
        r'(\d+)\s*views?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    
    return None


def parse_thread_row(row_element) -> Optional[Dict]:
    """Parse a single thread row from the forum list page"""
    try:
        # Find the title link - look for links that contain threadid parameter
        title_link = row_element.find('a', href=re.compile(r'threadid=\d+'))
        if not title_link:
            # Fallback: find any link in the row
            title_link = row_element.find('a')
        
        if not title_link:
            return None
        
        title = title_link.get_text(strip=True)
        if not title:
            return None
        
        # Get URL and make it absolute
        href = title_link.get('href', '')
        if not href:
            return None
        
        if href.startswith('http://') or href.startswith('https://'):
            url = href
        else:
            url = urljoin(HUAREN_BASE_URL, href)
        
        # Generate stable ID
        thread_id = generate_thread_id(url, title)
        
        # Try to extract reply count and view count
        row_text = row_element.get_text()
        reply_count = extract_reply_count(row_text)
        view_count = extract_view_count(row_text)
        
        # Try to extract author (look for common patterns)
        author = None
        author_elem = row_element.find(class_=re.compile(r'author|user|poster', re.I))
        if author_elem:
            author = author_elem.get_text(strip=True)
        
        # Try to extract last post time
        published_at = None
        time_elem = row_element.find(class_=re.compile(r'time|date|posted', re.I))
        if time_elem:
            time_text = time_elem.get_text(strip=True)
            # Try to parse common date formats
            try:
                from dateutil import parser
                published_at = parser.parse(time_text)
                # Make timezone-aware
                if published_at.tzinfo is None:
                    published_at = pytz.UTC.localize(published_at)
            except:
                pass
        
        return {
            "id": thread_id,
            "title": title,
            "url": url,
            "published_at": published_at.isoformat() if published_at else None,
            "reply_count": reply_count,
            "view_count": view_count,
            "author": author
        }
    except Exception as e:
        print(f"Error parsing thread row: {e}")
        return None


def fetch_huaren_forum(forumid: int, page: int = 1) -> List[Dict]:
    """
    Fetch and parse Huaren forum threads
    Returns list of thread objects
    """
    cache_key = get_cache_key(forumid, page)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    # Check rate limit
    if not check_rate_limit():
        # Return cached data if available, or empty list
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass
        return []
    
    try:
        # Build URL
        url = f"{HUAREN_BASE_URL}/showforum.html?forumid={forumid}"
        if page > 1:
            url += f"&page={page}"
        
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": HUAREN_BASE_URL
        }
        
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            
            # Parse HTML
            soup = BeautifulSoup(html, 'lxml')
            
            # Find thread rows - look for common forum list patterns
            threads = []
            
            # Strategy 1: Look for table rows with thread links
            rows = soup.find_all('tr')
            for row in rows:
                # Check if row contains a thread link
                if row.find('a', href=re.compile(r'threadid=\d+')):
                    thread = parse_thread_row(row)
                    if thread:
                        threads.append(thread)
            
            # Strategy 2: If no rows found, look for list items
            if not threads:
                list_items = soup.find_all(['li', 'div'], class_=re.compile(r'thread|post|item', re.I))
                for item in list_items:
                    if item.find('a', href=re.compile(r'threadid=\d+')):
                        thread = parse_thread_row(item)
                        if thread:
                            threads.append(thread)
            
            # Deduplicate by URL
            seen_urls = set()
            unique_threads = []
            for thread in threads:
                url_normalized = thread['url'].lower().split('?')[0].split('#')[0]
                if url_normalized not in seen_urls:
                    seen_urls.add(url_normalized)
                    unique_threads.append(thread)
            
            # Cache results
            if redis_client:
                redis_client.setex(cache_key, CACHE_TTL, json.dumps(unique_threads, default=str))
            
            return unique_threads
            
    except Exception as e:
        print(f"Error fetching Huaren forum {forumid}: {e}")
        import traceback
        traceback.print_exc()
        
        # Return cached data if available
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass
        
        # Return empty list on error (graceful fallback)
        return []


def rank_gossip_threads(threads: List[Dict]) -> List[Dict]:
    """
    Rank gossip threads by engagement and recency
    score = reply_count_weight + recency_weight
    """
    now = datetime.now(pytz.UTC)
    
    def calculate_score(thread: Dict) -> float:
        score = 0.0
        
        # Reply count weight (0-50)
        reply_count = thread.get('reply_count', 0) or 0
        if reply_count > 0:
            # Logarithmic scale: log10(reply_count + 1) * 10
            import math
            score += math.log10(reply_count + 1) * 10
        
        # Recency weight (0-50)
        published_at = thread.get('published_at')
        if published_at:
            try:
                if isinstance(published_at, str):
                    pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                else:
                    pub_date = published_at
                
                if pub_date.tzinfo is None:
                    pub_date = pytz.UTC.localize(pub_date)
                
                age_hours = (now - pub_date).total_seconds() / 3600
                
                if age_hours < 24:
                    score += 50  # Very recent
                elif age_hours < 72:
                    score += 30  # Recent
                elif age_hours < 168:  # 7 days
                    score += 10  # Moderate
                # Older threads get 0 recency score
            except:
                pass
        
        return score
    
    # Sort by score (descending)
    scored_threads = [(thread, calculate_score(thread)) for thread in threads]
    scored_threads.sort(key=lambda x: x[1], reverse=True)
    
    return [thread for thread, _ in scored_threads]


def filter_gossip_threads(threads: List[Dict]) -> List[Dict]:
    """
    Quality filter for gossip threads
    - Drop threads with empty title
    - Deduplicate by normalized title
    """
    filtered = []
    seen_titles = set()
    
    for thread in threads:
        title = thread.get('title', '').strip()
        
        # Drop empty titles
        if not title:
            continue
        
        # Deduplicate by normalized title
        normalized_title = title.lower().strip()
        if normalized_title in seen_titles:
            continue
        
        seen_titles.add(normalized_title)
        filtered.append(thread)
    
    return filtered


def fetch_gossip_forum(forumid: int = 398, page: int = 1, limit: int = 10) -> List[Dict]:
    """
    Fetch gossip threads from Huaren forum
    Applies ranking and quality filters
    """
    # Fetch threads
    threads = fetch_huaren_forum(forumid=forumid, page=page)
    
    # Quality filter
    filtered = filter_gossip_threads(threads)
    
    # Rank by engagement and recency
    ranked = rank_gossip_threads(filtered)
    
    # Add source info
    for thread in ranked:
        thread['source'] = 'huaren'
        thread['forumid'] = forumid
    
    return ranked[:limit]

