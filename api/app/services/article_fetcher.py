import httpx
import hashlib
import re
from typing import Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import trafilatura
from bs4 import BeautifulSoup
import json

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def normalize_url(url: str) -> str:
    """Remove tracking parameters and normalize URL"""
    try:
        parsed = urlparse(url)
        # Remove common tracking params
        tracking_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ref', 'source', 'campaign', 'xhsshare'
        }
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}
        
        new_query = urlencode(cleaned_params, doseq=True)
        new_parsed = parsed._replace(query=new_query, fragment='')
        return urlunparse(new_parsed)
    except Exception:
        return url


def detect_platform(url: str) -> str:
    """
    Detect platform from URL hostname
    Returns: 'youtube', 'tiktok', 'instagram', or 'web'
    """
    if not url:
        return 'web'
    
    url_lower = url.lower()
    
    # YouTube detection (youtube.com or youtu.be)
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    
    # TikTok detection
    if 'tiktok.com' in url_lower:
        return 'tiktok'
    
    # Instagram detection
    if 'instagram.com' in url_lower:
        return 'instagram'
    
    # Default to web for all other sources
    return 'web'


def extract_video_id(url: str, platform: str) -> Optional[str]:
    """
    Extract video ID from platform URL
    
    Returns:
        Video ID string or None
    """
    if not url or not platform:
        return None
    
    try:
        if platform == 'youtube':
            # YouTube URL patterns:
            # https://www.youtube.com/watch?v=VIDEO_ID
            # https://youtu.be/VIDEO_ID
            # https://www.youtube.com/embed/VIDEO_ID
            parsed = urlparse(url)
            
            if 'youtu.be' in parsed.netloc:
                # Short URL: youtu.be/VIDEO_ID
                video_id = parsed.path.lstrip('/').split('?')[0]
                return video_id if video_id else None
            
            # Regular YouTube URL
            query_params = parse_qs(parsed.query)
            if 'v' in query_params:
                return query_params['v'][0]
            
            # Embed URL: youtube.com/embed/VIDEO_ID
            if '/embed/' in parsed.path:
                video_id = parsed.path.split('/embed/')[-1].split('?')[0]
                return video_id if video_id else None
        
        elif platform == 'tiktok':
            # TikTok URL patterns:
            # https://www.tiktok.com/@username/video/VIDEO_ID
            # https://vm.tiktok.com/CODE
            parsed = urlparse(url)
            
            if '/video/' in parsed.path:
                # Extract video ID from path
                parts = parsed.path.split('/video/')
                if len(parts) > 1:
                    video_id = parts[-1].split('?')[0]
                    return video_id if video_id else None
        
        elif platform == 'instagram':
            # Instagram doesn't have a simple video ID in URL
            # We'll use the post shortcode instead
            # https://www.instagram.com/p/SHORTCODE/
            # https://www.instagram.com/reel/SHORTCODE/
            parsed = urlparse(url)
            
            # Extract shortcode from /p/ or /reel/
            for pattern in ['/p/', '/reel/']:
                if pattern in parsed.path:
                    shortcode = parsed.path.split(pattern)[-1].split('/')[0].split('?')[0]
                    return shortcode if shortcode else None
    
    except Exception as e:
        print(f"Error extracting video ID from {url}: {e}")
    
    return None


def extract_thumbnail_url(url: str, platform: str, video_id: Optional[str] = None) -> Optional[str]:
    """
    Generate thumbnail URL for platform content
    
    Returns:
        Thumbnail URL string or None
    """
    if not url or not platform:
        return None
    
    try:
        if platform == 'youtube' and video_id:
            # YouTube thumbnail: https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        elif platform == 'tiktok':
            # TikTok doesn't have a simple thumbnail API
            # We'll need to fetch from oEmbed or use a placeholder
            return None
        
        elif platform == 'instagram':
            # Instagram doesn't have a simple thumbnail API
            # We'll need to fetch from oEmbed or use a placeholder
            return None
    
    except Exception as e:
        print(f"Error generating thumbnail URL for {url}: {e}")
    
    return None


def is_valid_content_url(url: str) -> bool:
    """
    Check if URL points to actual content (not homepage/explore pages)
    Returns False for invalid URLs that should be skipped
    """
    if not url:
        return False
    
    # Generic filtering for common invalid patterns
    invalid_patterns = [
        '/home',
        '/search',
    ]
    
    if any(pattern in url for pattern in invalid_patterns):
        return False
    
    return True


def fetch_article(url: str, timeout: int = 10) -> Tuple[Optional[str], Optional[str], Optional[datetime]]:
    """
    Fetch article content from URL
    
    Returns:
        Tuple of (cleaned_text, title, published_at)
    """
    try:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
            
            # Try trafilatura first (best for article extraction)
            try:
                extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
                if extracted:
                    title = trafilatura.extract_metadata(html)
                    title_text = title.title if title else None
                    
                    # Try to extract date
                    published_at = None
                    if title and hasattr(title, 'date'):
                        published_at = title.date
                    
                    return extracted, title_text, published_at
            except Exception:
                pass
            
            # Fallback to BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract title
            title = None
            for tag in ['title', 'h1', 'meta[property="og:title"]']:
                elem = soup.select_one(tag)
                if elem:
                    title = elem.get_text() if hasattr(elem, 'get_text') else elem.get('content', '')
                    if title:
                        break
            
            # Extract main content
            # Try site-specific selectors first
            main_content = None
            
            # 1point3acres specific selectors
            if '1point3acres.com' in url:
                site_specific_selectors = [
                    '.thread-content',  # Main thread content
                    '.post-content',    # Post content
                    '#thread-content',  # Thread content by ID
                    '.thread-body',     # Thread body
                    '[class*="thread"]', # Any thread-related class
                    '[class*="post-body"]', # Post body
                    '[id*="post"]',     # Post by ID
                ]
                for selector in site_specific_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        main_content = elem
                        break
            
            # Generic selectors
            if not main_content:
                content_selectors = [
                    'article',
                    '[role="main"]',
                    '.content',
                    '.post-content',
                    '#content',
                    'main',
                    '[class*="content"]',
                    '[class*="article"]',
                ]
                
                for selector in content_selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        main_content = elem
                        break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Remove script and style elements, plus navigation
                for script in main_content(["script", "style", "nav", "footer", "header", "aside", 
                                           "form", "button", "[class*='nav']", "[class*='menu']",
                                           "[class*='sidebar']", "[class*='header']", "[class*='footer']"]):
                    script.decompose()
                
                text = main_content.get_text(separator='\n', strip=True)
                # Clean up whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = text.strip()
                
                # For 1point3acres, try to extract just the post text, removing navigation
                if '1point3acres.com' in url and len(text) < 1000:
                    # Try to find the actual post text in common patterns
                    post_patterns = [
                        soup.select_one('[class*="message"]'),
                        soup.select_one('[class*="post"]'),
                        soup.select_one('[id*="post"]'),
                        soup.select_one('[class*="thread"]'),
                    ]
                    for pattern in post_patterns:
                        if pattern:
                            post_text = pattern.get_text(separator='\n', strip=True)
                            if len(post_text) > len(text) and len(post_text) > 200:
                                text = post_text
                                break
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Check for login-required pages (common patterns)
            login_indicators = [
                '您需要 登录',
                '需要 登录',
                '没有帐号',
                'login required',
                'please log in',
                'sign in to view',
                'register to view'
            ]
            
            # If content is mostly login prompt, return None
            if text and any(indicator in text for indicator in login_indicators):
                # Check if login prompt is a significant portion of content
                text_lower = text.lower()
                login_portion = sum(len(ind) for ind in login_indicators if ind.lower() in text_lower)
                if len(text) < 500 or login_portion > len(text) * 0.3:
                    print(f"Skipping {url}: login-required page")
                    return None, None, None
            
            # Try to extract published date
            published_at = None
            date_selectors = [
                'time[datetime]',
                'meta[property="article:published_time"]',
                'meta[name="publish-date"]',
                '[class*="date"]',
                '[class*="published"]'
            ]
            
            for selector in date_selectors:
                elem = soup.select_one(selector)
                if elem:
                    date_str = elem.get('datetime') or elem.get('content') or elem.get_text()
                    if date_str:
                        try:
                            from dateutil import parser
                            published_at = parser.parse(date_str)
                            break
                        except:
                            pass
            
            return text[:50000], title, published_at  # Limit text size
            
    except Exception as e:
        print(f"Error fetching article {url}: {e}")
        return None, None, None


def compute_content_hash(title: Optional[str], text: Optional[str]) -> str:
    """Compute SHA256 hash of content for deduplication"""
    content = (title or "") + (text[:2000] if text else "")
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def extract_entities(text: Optional[str], title: Optional[str]) -> Tuple[list, list, list]:
    """
    Extract entities: companies, cities, and general tags
    
    Returns:
        Tuple of (company_tags, city_hints, general_tags)
    """
    if not text and not title:
        return [], [], []
    
    full_text = ((title or "") + " " + (text or "")).lower()
    
    # Company names
    companies = [
        'meta', 'facebook', 'google', 'alphabet', 'apple', 'amazon', 'microsoft',
        'netflix', 'tesla', 'nvidia', 'amd', 'intel', 'oracle', 'salesforce',
        'adobe', 'uber', 'lyft', 'airbnb', 'doordash', 'instacart', 'stripe',
        'palantir', 'databricks', 'openai', 'anthropic', 'linkedin', 'twitter',
        'x', 'snapchat', 'tiktok', 'bytedance', 'zoom', 'slack', 'notion'
    ]
    
    company_tags = [c for c in companies if c in full_text]
    
    # Bay Area cities
    cities = [
        'sunnyvale', 'cupertino', 'san jose', 'palo alto', 'mountain view',
        'fremont', 'santa clara', 'redwood city', 'menlo park', 'foster city',
        'san mateo', 'burlingame', 'millbrae', 'san francisco', 'sf', 'oakland',
        'berkeley', 'alameda', 'hayward', 'union city', 'newark'
    ]
    
    city_hints = [c for c in cities if c in full_text]
    
    # General tags (keywords)
    keywords = [
        'h1b', 'layoff', 'new grad', 'ng', 'offer', 'comp', 'promo', 'promotion',
        'interview', 'onsite', 'boba', '奶茶', '新开', 'food', 'restaurant',
        'coupon', 'deal', 'bogo', 'discount'
    ]
    
    general_tags = [k for k in keywords if k in full_text]
    
    return list(set(company_tags)), list(set(city_hints)), list(set(general_tags))


def extract_food_entities(text: Optional[str], title: Optional[str]) -> Tuple[list, list, list, Optional[str]]:
    """
    Extract food-focused entities: cities, food tags, and possible place name
    This is a lightweight adapter for food content, not changing global extraction
    
    Returns:
        Tuple of (city_hints, food_tags, general_tags, place_name)
        - city_hints: Bay Area cities only
        - food_tags: food-related keywords (boba, cafe, restaurant, dessert, etc.)
        - general_tags: other relevant tags
        - place_name: possible restaurant/place name (heuristic only, may be None)
    """
    if not text and not title:
        return [], [], [], None
    
    full_text = ((title or "") + " " + (text or "")).lower()
    
    # Bay Area cities (same as general extraction)
    cities = [
        'sunnyvale', 'cupertino', 'san jose', 'palo alto', 'mountain view',
        'fremont', 'santa clara', 'redwood city', 'menlo park', 'foster city',
        'san mateo', 'burlingame', 'millbrae', 'san francisco', 'sf', 'oakland',
        'berkeley', 'alameda', 'hayward', 'union city', 'newark'
    ]
    
    city_hints = [c for c in cities if c in full_text]
    
    # Chinese food-related tags (focused on Bay Area Chinese food)
    food_keywords = [
        'boba', '奶茶', 'dim sum', 'hot pot', '火锅', '麻辣烫', '川菜', '粤菜',
        '湘菜', '鲁菜', '东北菜', '上海菜', '北京菜', '烤鸭', '小笼包', '拉面',
        'ramen', 'pho', '中餐', 'chinese food', 'chinese restaurant', '探店',
        '美食', '新开', '新店', '推荐', 'review', 'vlog', 'foodie', 'cafe',
        'restaurant', 'dining', 'food', 'dessert', 'bakery', 'brunch', 'lunch',
        'dinner', 'breakfast', 'eat', 'drink'
    ]
    
    food_tags = [k for k in food_keywords if k in full_text]
    
    # General tags (non-food related but still useful)
    general_keywords = [
        'new', 'opening', 'opened', 'review', 'recommend', 'best', 'top',
        'must try', 'hidden gem', 'popular', 'trending'
    ]
    
    general_tags = [k for k in general_keywords if k in full_text]
    
    # Try to extract place name (heuristic: look for quoted text or "at [Name]" patterns)
    place_name = None
    import re
    
    # Pattern 1: "at [Place Name]" or "from [Place Name]"
    place_patterns = [
        r'at\s+([A-Z][a-zA-Z\s&]+?)(?:\s+in|\s+on|\s+at|\.|,|$)',
        r'from\s+([A-Z][a-zA-Z\s&]+?)(?:\s+in|\s+on|\.|,|$)',
        r'"([A-Z][a-zA-Z\s&]+?)"',  # Quoted names
    ]
    
    for pattern in place_patterns:
        matches = re.findall(pattern, title or "", re.IGNORECASE)
        if matches:
            # Take first match, clean it up
            candidate = matches[0].strip()
            # Skip if it's too long (probably not a place name) or contains common words
            if len(candidate) < 50 and candidate.lower() not in ['the', 'a', 'an', 'this', 'that']:
                place_name = candidate
                break
    
    return list(set(city_hints)), list(set(food_tags)), list(set(general_tags)), place_name

