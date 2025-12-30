"""
RSS Feed Fetcher Service
Fetches news from multiple RSS sources with caching and error handling
"""
import os
import redis
import json
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pytz
from xml.etree import ElementTree as ET
import re

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# RSS Feed Sources
RSS_SOURCES = {
    "techcrunch": {
        "url": "https://techcrunch.com/feed/",
        "name": "TechCrunch",
        "category": "tech"
    },
    "theverge": {
        "url": "https://www.theverge.com/rss/index.xml",
        "name": "The Verge",
        "category": "tech"
    },
    "arstechnica": {
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "name": "Ars Technica",
        "category": "tech"
    },
    "reuters_tech": {
        "url": "https://www.reuters.com/tools/rss/technology",
        "name": "Reuters Technology",
        "category": "tech"
    },
}

# Cache TTL: 10 minutes for feed data
RSS_CACHE_TTL = 600


def parse_rss_item(item_elem) -> Optional[Dict]:
    """Parse a single RSS item element"""
    try:
        # Get title
        title_elem = item_elem.find("title")
        title = title_elem.text if title_elem is not None else ""
        
        # Get link
        link_elem = item_elem.find("link")
        url = link_elem.text if link_elem is not None else ""
        
        # Get description
        desc_elem = item_elem.find("description")
        description = desc_elem.text if desc_elem is not None else ""
        # Remove HTML tags
        description = re.sub(r'<[^>]+>', '', description)
        
        # Get pubDate
        pub_date_elem = item_elem.find("pubDate")
        published_at = datetime.now(pytz.UTC)
        if pub_date_elem is not None and pub_date_elem.text:
            try:
                from dateutil import parser
                published_at = parser.parse(pub_date_elem.text)
                if published_at.tzinfo is None:
                    published_at = pytz.UTC.localize(published_at)
            except:
                pass
        
        return {
            "title": title.strip(),
            "url": url.strip(),
            "description": description.strip(),
            "published_at": published_at,
        }
    except Exception as e:
        print(f"Error parsing RSS item: {e}")
        return None


def fetch_rss_feed(source_key: str, timeout: float = 5.0) -> List[Dict]:
    """
    Fetch RSS feed from a source
    Returns list of news items
    """
    if source_key not in RSS_SOURCES:
        return []
    
    source = RSS_SOURCES[source_key]
    cache_key = f"rss:{source_key}:{datetime.now(pytz.UTC).strftime('%Y%m%d%H%M')}"  # Cache per 10 min
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                items = json.loads(cached)
                # Convert ISO strings back to datetime
                for item in items:
                    if isinstance(item.get("published_at"), str):
                        try:
                            from dateutil import parser
                            item["published_at"] = parser.parse(item["published_at"])
                        except:
                            item["published_at"] = datetime.now(pytz.UTC)
                return items
            except:
                pass
    
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(source["url"])
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Handle both RSS and Atom formats
            items = []
            if root.tag == "rss":
                # RSS format
                channel = root.find("channel")
                if channel is not None:
                    for item_elem in channel.findall("item"):
                        parsed = parse_rss_item(item_elem)
                        if parsed:
                            parsed["source"] = source["name"]
                            parsed["source_key"] = source_key
                            items.append(parsed)
            elif root.tag == "{http://www.w3.org/2005/Atom}feed":
                # Atom format
                for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                    try:
                        title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                        link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                        updated_elem = entry.find("{http://www.w3.org/2005/Atom}updated")
                        
                        title = title_elem.text if title_elem is not None else ""
                        url = link_elem.get("href") if link_elem is not None else ""
                        
                        published_at = datetime.now(pytz.UTC)
                        if updated_elem is not None and updated_elem.text:
                            try:
                                from dateutil import parser
                                published_at = parser.parse(updated_elem.text)
                                if published_at.tzinfo is None:
                                    published_at = pytz.UTC.localize(published_at)
                            except:
                                pass
                        
                        items.append({
                            "title": title.strip(),
                            "url": url.strip(),
                            "description": "",
                            "published_at": published_at,
                            "source": source["name"],
                            "source_key": source_key,
                        })
                    except:
                        continue
            
            # Filter to last 24 hours
            now = datetime.now(pytz.UTC)
            items = [
                item for item in items
                if (now - item["published_at"]).total_seconds() < 24 * 3600
            ]
            
            # Cache results
            if redis_client and items:
                # Convert datetime to ISO string for JSON
                cache_data = []
                for item in items:
                    cache_item = item.copy()
                    cache_item["published_at"] = item["published_at"].isoformat()
                    cache_data.append(cache_item)
                redis_client.setex(cache_key, RSS_CACHE_TTL, json.dumps(cache_data))
            
            return items
            
    except Exception as e:
        print(f"Error fetching RSS feed {source_key}: {e}")
        return []
    
    return []


def fetch_all_rss_feeds(limit_per_source: int = 20) -> List[Dict]:
    """
    Fetch from all RSS sources in parallel
    Returns combined list of news items
    """
    all_items = []
    
    for source_key in RSS_SOURCES.keys():
        try:
            items = fetch_rss_feed(source_key)
            all_items.extend(items[:limit_per_source])
        except Exception as e:
            print(f"Error fetching {source_key}: {e}")
            continue
    
    return all_items
