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
            'fbclid', 'gclid', 'ref', 'source', 'campaign'
        }
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}
        
        new_query = urlencode(cleaned_params, doseq=True)
        new_parsed = parsed._replace(query=new_query, fragment='')
        return urlunparse(new_parsed)
    except Exception:
        return url


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
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.post-content',
                '#content',
                'main'
            ]
            
            main_content = None
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    main_content = elem
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                # Remove script and style elements
                for script in main_content(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                
                text = main_content.get_text(separator='\n', strip=True)
                # Clean up whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = text.strip()
            else:
                text = soup.get_text(separator='\n', strip=True)
            
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

