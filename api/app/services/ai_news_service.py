"""
AI News Aggregation Service
Aggregates AI-related news from multiple sources: Google CSE, Finnhub, Hacker News
"""
import os
import redis
import json
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse
import hashlib
import pytz

from app.services.google_search import search_google, fetch_multiple_pages, check_budget_exceeded
from app.services.tech_trending_service import fetch_hn_stories
from app.services.stock_service import get_stock_news

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Priority news domains for AI news (top sources)
PRIORITY_DOMAINS = [
    "cnn.com", "techcrunch.com", "wsj.com", "reuters.com", 
    "bloomberg.com", "nytimes.com", "theverge.com", "bbc.com"
]

# Reputable news domains (allowlist)
REPUTABLE_DOMAINS = [
    "reuters.com", "bloomberg.com", "techcrunch.com", "theverge.com",
    "wired.com", "arstechnica.com", "engadget.com", "cnet.com",
    "bbc.com", "cnn.com", "nytimes.com", "wsj.com", "ft.com",
    "forbes.com", "businessinsider.com", "axios.com", "theguardian.com",
    "venturebeat.com", "zdnet.com", "infoworld.com", "theregister.com",
    "ieee.org", "nature.com", "science.org", "mit.edu", "stanford.edu"
]

# Blocklist domains (noise/spam)
BLOCKLIST_DOMAINS = [
    "facebook.com", "twitter.com", "linkedin.com", "reddit.com",
    "youtube.com", "tiktok.com", "instagram.com", "pinterest.com"
]

# AI-related keywords for filtering
AI_KEYWORDS = [
    "AI", "artificial intelligence", "LLM", "OpenAI", "Anthropic",
    "Nvidia", "AI regulation", "machine learning", "deep learning",
    "GPT", "Claude", "Gemini", "ChatGPT", "AGI", "neural network"
]


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication"""
    if not url:
        return ""
    parsed = urlparse(url)
    # Remove query params and fragments
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return normalized.lower()


def get_content_hash(title: str, domain: str) -> str:
    """Generate hash from title and domain for deduplication"""
    content = f"{title.lower().strip()}:{domain.lower()}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return ""


def is_ai_related(title: str, snippet: str = "") -> bool:
    """Check if content is AI-related"""
    text = f"{title} {snippet}".lower()
    return any(keyword.lower() in text for keyword in AI_KEYWORDS)


def is_reputable_source(domain: str) -> bool:
    """Check if domain is in reputable sources list"""
    if not domain:
        return False
    return any(reputable in domain for reputable in REPUTABLE_DOMAINS)


def is_blocked_domain(domain: str) -> bool:
    """Check if domain is in blocklist"""
    if not domain:
        return True
    return any(blocked in domain for blocked in BLOCKLIST_DOMAINS)


def parse_time_ago(published_at: Optional[datetime]) -> str:
    """Convert datetime to relative time string"""
    if not published_at:
        return ""
    
    try:
        if isinstance(published_at, str):
            try:
                from dateutil import parser
                published_at = parser.parse(published_at)
            except:
                # Fallback to simple parsing
                try:
                    published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except:
                    return ""
        
        if not isinstance(published_at, datetime):
            return ""
        
        now = datetime.now(pytz.UTC)
        if published_at.tzinfo is None:
            published_at = pytz.UTC.localize(published_at)
        delta = now - published_at
        
        if delta.days > 0:
            return f"{delta.days}天前"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours}小时前"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes}分钟前"
        else:
            return "刚刚"
    except:
        return ""


def extract_ticker_from_title(title: str) -> Optional[str]:
    """Extract stock ticker from title if mentioned"""
    ticker_map = {
        'nvidia': 'NVDA', 'openai': 'MSFT', 'microsoft': 'MSFT',
        'google': 'GOOG', 'alphabet': 'GOOG', 'meta': 'META',
        'facebook': 'META', 'amazon': 'AMZN', 'apple': 'AAPL',
        'amd': 'AMD', 'tsla': 'TSLA', 'tesla': 'TSLA',
        'anthropic': 'ANTH', 'anthropic ai': 'ANTH'
    }
    title_lower = title.lower()
    for key, ticker in ticker_map.items():
        if key in title_lower:
            return ticker
    return None


def fetch_ai_news_from_cse(limit: int = 15, date_restrict: str = "d1", priority_domains: Optional[List[str]] = None) -> List[Dict]:
    """Fetch AI news using Google CSE from priority domains
    
    Args:
        limit: Number of items to fetch
        date_restrict: Date restriction ("d1" for 1 day, "d3" for 3 days)
        priority_domains: List of priority domains to search (e.g., ["cnn.com", "techcrunch.com"])
    """
    if check_budget_exceeded():
        print("WARNING: CSE budget exceeded, skipping AI news from CSE")
        return []
    
    if priority_domains is None:
        priority_domains = PRIORITY_DOMAINS
    
    # AI-related query
    query = 'AI OR "artificial intelligence" OR LLM OR OpenAI OR Anthropic OR Nvidia OR "AI regulation" OR "machine learning" OR GPT OR ChatGPT'
    
    all_items = []
    seen_urls = set()
    seen_hashes = set()
    
    # Search each priority domain
    for site_domain in priority_domains:
        if len(all_items) >= limit * 2:
            break
            
        try:
            results = fetch_multiple_pages(
                query=query,
                site_domain=site_domain,  # Search within specific domain
                max_results=10,  # Max 10 per domain
                date_restrict=date_restrict
            )
            
            for item in results:
                url = item.get("link", "")
                if not url:
                    continue
                
                item_domain = extract_domain(url)
                if is_blocked_domain(item_domain):
                    continue
                
                title = item.get("title", "").strip()
                snippet = item.get("snippet", "")
                
                if not title or not is_ai_related(title, snippet):
                    continue
                
                # Deduplicate
                normalized_url = normalize_url(url)
                content_hash = get_content_hash(title, item_domain)
                
                if normalized_url in seen_urls or content_hash in seen_hashes:
                    continue
                
                seen_urls.add(normalized_url)
                seen_hashes.add(content_hash)
                
                # Try to extract published date from snippet or use current time
                published_at = datetime.now(pytz.UTC)
                
                all_items.append({
                    "title": title,
                    "url": url,
                    "domain": item_domain,
                    "source": item_domain.split(".")[0].title() if item_domain else "Unknown",
                    "snippet": snippet,
                    "published_at": published_at,
                    "is_reputable": is_reputable_source(item_domain),
                    "ticker": extract_ticker_from_title(title)
                })
                
                if len(all_items) >= limit * 2:
                    break
            
            if len(all_items) >= limit * 2:
                break
        except Exception as e:
            print(f"Error fetching AI news from CSE for {site_domain}: {e}")
            continue
    
    return all_items


def fetch_ai_news_from_finnhub(limit: int = 10, range_hours: int = 24) -> List[Dict]:
    """Fetch AI news from Finnhub stock news (filtered by AI keywords)
    
    Args:
        limit: Number of items to fetch
        range_hours: Look back window in hours (24 for 1 day, 72 for 3 days)
    """
    ai_tickers = ["NVDA", "MSFT", "GOOG", "META", "AMZN", "AAPL"]
    all_items = []
    seen_urls = set()
    
    for ticker in ai_tickers[:3]:  # Limit to 3 tickers
        try:
            news_items = get_stock_news(ticker, range_hours=range_hours)
            
            for item in news_items:
                title = item.headline or ""
                if not title or not is_ai_related(title, item.summary or ""):
                    continue
                
                url = item.url or ""
                if not url or url in seen_urls:
                    continue
                
                domain = extract_domain(url)
                if is_blocked_domain(domain):
                    continue
                
                seen_urls.add(url)
                
                all_items.append({
                    "title": title,
                    "url": url,
                    "domain": domain,
                    "source": item.source or domain.split(".")[0].title() if domain else "Unknown",
                    "snippet": item.summary or "",
                    "published_at": item.published_at or datetime.now(pytz.UTC),
                    "is_reputable": is_reputable_source(domain),
                    "ticker": ticker
                })
                
                if len(all_items) >= limit:
                    break
            
            if len(all_items) >= limit:
                break
        except Exception as e:
            print(f"Error fetching AI news from Finnhub for {ticker}: {e}")
            continue
    
    return all_items


def fetch_ai_news_from_hn(limit: int = 10) -> List[Dict]:
    """Fetch AI news from Hacker News (fallback)"""
    try:
        stories = fetch_hn_stories(limit=limit * 2)
        all_items = []
        seen_urls = set()
        
        for story in stories:
            title = story.get("title", "").strip()
            if not title or not is_ai_related(title):
                continue
            
            url = story.get("url", "")
            if not url or url in seen_urls:
                continue
            
            domain = extract_domain(url)
            if is_blocked_domain(domain):
                continue
            
            seen_urls.add(url)
            
            # Parse created_at
            published_at = datetime.now(pytz.UTC)
            try:
                if story.get("createdAt"):
                    from dateutil import parser
                    parsed = parser.parse(story["createdAt"])
                    # Ensure timezone-aware
                    if parsed.tzinfo is None:
                        parsed = pytz.UTC.localize(parsed)
                    published_at = parsed
            except:
                pass
            
            all_items.append({
                "title": title,
                "url": url,
                "domain": domain,
                "source": "Hacker News",
                "snippet": story.get("summary", ""),
                "published_at": published_at,
                "is_reputable": is_reputable_source(domain),
                "ticker": extract_ticker_from_title(title)
            })
            
            if len(all_items) >= limit:
                break
        
        return all_items
    except Exception as e:
        print(f"Error fetching AI news from HN: {e}")
        return []


def aggregate_ai_news(limit: int = 5, target_min: int = 4) -> List[Dict]:
    """
    Aggregate AI news from priority sources: Google CSE (CNN, TechCrunch, WSJ, etc.), Hacker News, and Finnhub
    Returns 4-6 items (target=5, minimum=4)
    
    Pipeline:
    1. Primary: Google CSE from priority domains (1 day)
    2. Fallback 1: Hacker News
    3. Fallback 2: Expand CSE to 3 days
    4. Fallback 3: Finnhub stock news (broader ticker list)
    5. Fallback 4: General CSE search (no domain restriction)
    """
    cache_key = f"ai_news:aggregated:{datetime.now(pytz.UTC).strftime('%Y%m%d%H')}"
    
    # Check cache (1 hour cache)
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                cached_items = json.loads(cached)
                # Convert ISO strings back to datetime objects
                for item in cached_items:
                    if isinstance(item.get("published_at"), str):
                        try:
                            from dateutil import parser
                            item["published_at"] = parser.parse(item["published_at"])
                        except:
                            item["published_at"] = datetime.now(pytz.UTC)
                # Return cached items, but ensure we have at least target_min
                if len(cached_items) >= target_min:
                    return cached_items[:limit]
                # If cached has fewer than target_min, continue to fetch more
            except:
                pass
    
    all_items = []
    seen_urls = set()
    seen_hashes = set()
    
    # Helper to add item with deduplication
    def add_item(item: Dict):
        normalized_url = normalize_url(item["url"])
        content_hash = get_content_hash(item["title"], item["domain"])
        if normalized_url not in seen_urls and content_hash not in seen_hashes:
            seen_urls.add(normalized_url)
            seen_hashes.add(content_hash)
            all_items.append(item)
    
    # Priority 1: Google CSE from priority domains (1 day)
    date_restrict = "d1"
    cse_items = fetch_ai_news_from_cse(limit=max(limit * 3, 30), date_restrict=date_restrict, priority_domains=PRIORITY_DOMAINS)
    for item in cse_items:
        add_item(item)
    
    # Priority 2: Hacker News (if we need more)
    if len(all_items) < limit:
        hn_items = fetch_ai_news_from_hn(limit=max((limit - len(all_items)) * 2, 20))
        for item in hn_items:
            add_item(item)
            if len(all_items) >= limit * 2:  # Collect more for ranking
                break
    
    # Fallback 3: Expand CSE to 3 days (if still need more)
    if len(all_items) < limit:
        date_restrict = "d3"
        cse_items_3d = fetch_ai_news_from_cse(limit=max((limit - len(all_items)) * 2, 30), date_restrict=date_restrict, priority_domains=PRIORITY_DOMAINS)
        for item in cse_items_3d:
            add_item(item)
            if len(all_items) >= limit * 2:
                break
    
    # Fallback 4: Finnhub stock news (broader ticker list)
    if len(all_items) < target_min:
        # Broader ticker list: include more tech stocks
        broader_tickers = ["NVDA", "MSFT", "GOOG", "META", "AMZN", "AAPL", "TSLA", "AMD", "TSM", "AVGO"]
        for ticker in broader_tickers:
            if len(all_items) >= limit:
                break
            try:
                news_items = get_stock_news(ticker, range_hours=72)  # 3 days
                for item in news_items:
                    title = item.headline or ""
                    if not title:
                        continue
                    # Relaxed filter: check if title contains tech/AI keywords (not strict)
                    title_lower = title.lower()
                    tech_keywords = ["ai", "tech", "technology", "software", "chip", "semiconductor", 
                                    "cloud", "data", "digital", "innovation", "startup", "company"]
                    if any(kw in title_lower for kw in tech_keywords):
                        url = item.url or ""
                        if not url or url in seen_urls:
                            continue
                        domain = extract_domain(url)
                        if is_blocked_domain(domain):
                            continue
                        add_item({
                            "title": title,
                            "url": url,
                            "domain": domain,
                            "source": item.source or domain.split(".")[0].title() if domain else "Unknown",
                            "snippet": item.summary or "",
                            "published_at": item.published_at or datetime.now(pytz.UTC),
                            "is_reputable": is_reputable_source(domain),
                            "ticker": ticker
                        })
                        if len(all_items) >= limit * 2:
                            break
            except Exception as e:
                print(f"Error fetching Finnhub news for {ticker}: {e}")
                continue
    
    # Fallback 5: General CSE search (no domain restriction, if still needed)
    if len(all_items) < target_min:
        try:
            general_cse = fetch_ai_news_from_cse(limit=30, date_restrict="d3", priority_domains=None)
            for item in general_cse:
                add_item(item)
                if len(all_items) >= limit * 2:
                    break
        except Exception as e:
            print(f"Error in general CSE fallback: {e}")
    
    # Ranking: prefer priority domains (CNN, TechCrunch, WSJ, etc.) + recency
    def rank_item(item: Dict) -> tuple:
        score = 0
        # Priority domains get highest score
        if item.get("domain") in PRIORITY_DOMAINS:
            score += 20
        elif item.get("is_reputable"):
            score += 10
        # Recency: newer items get higher score
        now = datetime.now(pytz.UTC)
        published_at = item.get("published_at", now)
        # Ensure both datetimes are timezone-aware
        if published_at.tzinfo is None:
            published_at = pytz.UTC.localize(published_at)
        if now.tzinfo is None:
            now = pytz.UTC.localize(now)
        age_hours = (now - published_at).total_seconds() / 3600
        score += max(0, 5 - age_hours / 6)  # Decay over 30 hours
        return (-score, published_at)
    
    all_items.sort(key=rank_item)
    
    # Return top items (allow up to 3 items per domain if needed to reach target_min)
    domain_counts = {}
    final_items = []
    max_per_domain = 2  # Start with 2 per domain
    
    for item in all_items:
        domain = item["domain"]
        count = domain_counts.get(domain, 0)
        # If we haven't reached target_min, allow more items per domain
        if len(final_items) < target_min:
            max_per_domain = 3  # Increase to 3 per domain to reach minimum
        else:
            max_per_domain = 2  # Back to 2 per domain for diversity
        
        if count < max_per_domain:
            domain_counts[domain] = count + 1
            final_items.append(item)
            if len(final_items) >= limit:
                break
    
    # If still not enough, relax domain limit completely
    if len(final_items) < target_min:
        for item in all_items:
            if item not in final_items:
                final_items.append(item)
                if len(final_items) >= target_min:
                    break
    
    # Cache results (convert datetime to ISO string for JSON serialization)
    if redis_client and final_items:
        cacheable_items = []
        for item in final_items:
            cacheable_item = item.copy()
            if isinstance(cacheable_item.get("published_at"), datetime):
                cacheable_item["published_at"] = cacheable_item["published_at"].isoformat()
            cacheable_items.append(cacheable_item)
        redis_client.setex(cache_key, 3600, json.dumps(cacheable_items, default=str))
    
    return final_items[:limit]  # Return up to limit items

