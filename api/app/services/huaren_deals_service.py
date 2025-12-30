"""
Huaren.us Forum Deals Service
Fetches and parses deals from Huaren.us forum (forumid=395)
"""
import os
import json
import redis
import hashlib
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
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
HUAREN_FORUM_URL = f"{HUAREN_BASE_URL}/showforum.html?forumid=395"

# User agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_cache_key(forumid: int = 395, page: int = 1) -> str:
    """Get Redis cache key for Huaren forum"""
    return f"deals:huaren:forum{forumid}:page{page}"


def get_rate_limit_key() -> str:
    """Get rate limit key"""
    return "deals:huaren:ratelimit"


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
    
    # Fallback: hash of URL + title
    combined = f"{url}|{title}"
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
            # This is basic - could be enhanced with dateutil
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
            "source": "huaren",
            "subsource": "huaren_forum_395",
            "published_at": published_at.isoformat() if published_at else None,
            "reply_count": reply_count,
            "view_count": view_count,
            "author": author
        }
    except Exception as e:
        print(f"Error parsing thread row: {e}")
        return None


def fetch_huaren_forum(forumid: int = 395, page: int = 1) -> List[Dict]:
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
        print(f"Error fetching Huaren forum: {e}")
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


def map_huaren_thread_to_deal(thread: Dict) -> Dict:
    """
    Map Huaren thread to deal model
    Applies category inference, value extraction, and quality filters
    """
    title = thread.get('title', '').lower()
    title_original = thread.get('title', '')
    
    # Quality filters: drop generic/discussion threads
    generic_keywords = ['求', '问一下', '有人用过吗', '讨论', '闲聊', '求助', '请问', '问个问题']
    if any(kw in title_original for kw in generic_keywords):
        # Check if it also has deal keywords
        deal_keywords = ['deal', '折扣', '优惠', '返现', '开卡', 'bonus', 'bug价', '免单', '羊毛', 'bogo', '$', '%', 'coupon', 'code']
        if not any(kw in title_original.lower() for kw in deal_keywords):
            return None  # Filter out
    
    # Category inference
    category = None
    
    # Fast food keywords
    fast_food_keywords = ['麦当劳', 'mcd', 'bk', 'burger king', 'subway', 'chipotle', 'starbucks', '外卖', 'doordash', 'ubereats', 'bogo', '快餐']
    if any(kw in title for kw in fast_food_keywords):
        category = 'fast_food'
    
    # Costco/household keywords
    if not category:
        costco_keywords = ['costco', '纸巾', '洗衣液', '尿布', '日用品', 'bulk', 'wholesale']
        if any(kw in title for kw in costco_keywords):
            category = 'grocery'
    
    # Subscriptions/software keywords
    if not category:
        sub_keywords = ['会员', '年费', '订阅', 'netflix', 'disney', 'vpn', '云盘', 'ai', 'chatgpt', 'subscription', 'software', 'saas']
        if any(kw in title for kw in sub_keywords):
            category = 'apps'
    
    # Finance keywords
    if not category:
        finance_keywords = ['开卡', 'bonus', 'checking', 'savings', '银行', 'credit card', '信用卡', '返现', '返钱']
        if any(kw in title for kw in finance_keywords):
            category = 'apps'  # Map to apps for now, could be separate category
    
    # Default to uncategorized if cannot infer
    if not category:
        category = 'uncategorized'
    
    # Value extraction
    price_or_value_text = None
    estimated_value_usd = None
    
    # Extract dollar amounts
    dollar_match = re.search(r'\$(\d+\.?\d*)', title_original)
    if dollar_match:
        try:
            amount = float(dollar_match.group(1))
            estimated_value_usd = amount
            price_or_value_text = f"${int(amount)}"
        except:
            pass
    
    # Extract percentage
    percent_match = re.search(r'(\d+)%\s*off', title_original, re.IGNORECASE)
    if percent_match:
        percent = int(percent_match.group(1))
        price_or_value_text = f"{percent}% off"
        # Rough estimate
        if percent >= 50:
            estimated_value_usd = 15
        elif percent >= 20:
            estimated_value_usd = 10
        else:
            estimated_value_usd = 5
    
    # Check for BOGO, Free, etc.
    if 'bogo' in title or '买一送一' in title_original or '买1送1' in title_original:
        price_or_value_text = 'BOGO'
        estimated_value_usd = 15
    elif 'free' in title or '免费' in title_original or '免邮' in title_original:
        price_or_value_text = 'Free'
        estimated_value_usd = 5
    
    # Engagement boost: prefer threads with replies
    reply_count = thread.get('reply_count', 0) or 0
    view_count = thread.get('view_count', 0) or 0
    
    # Build deal object
    deal = {
        "id": thread.get('id'),
        "title": title_original,
        "description": None,
        "url": thread.get('url'),
        "source": "huaren",
        "sourceUrl": thread.get('url'),
        "category": category,
        "imageUrl": None,
        "saveAmount": str(estimated_value_usd) if estimated_value_usd else None,
        "code": None,
        "published_at": thread.get('published_at'),
        "fetched_at": datetime.now(pytz.UTC).isoformat(),
        "reply_count": reply_count,
        "view_count": view_count,
        "author": thread.get('author'),
        "price_or_value_text": price_or_value_text,
        "estimated_value_usd": estimated_value_usd
    }
    
    # Quality filter: downrank if no replies and no clear value signal
    if reply_count == 0 and not price_or_value_text and not estimated_value_usd:
        # Still include but will be downranked by scoring
        pass
    
    return deal


def fetch_huaren_deals(limit: int = 30) -> List[Dict]:
    """
    Fetch Huaren forum deals, map to deal model, and apply quality filters
    Returns list of deal objects ready for unified processing
    """
    # Fetch threads from forum
    threads = fetch_huaren_forum(forumid=395, page=1)
    
    # Map to deals
    deals = []
    for thread in threads:
        deal = map_huaren_thread_to_deal(thread)
        if deal:
            deals.append(deal)
    
    # Sort by engagement (reply_count) and limit
    deals.sort(key=lambda x: (x.get('reply_count', 0) or 0, x.get('view_count', 0) or 0), reverse=True)
    
    return deals[:limit]

