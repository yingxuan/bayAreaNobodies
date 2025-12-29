"""
Tech Trending Service - fetch trending tech news from Hacker News
Uses HN Algolia API to fetch front page stories
"""
import os
import redis
import json
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz

# Optional imports for translation
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 10 minutes (600 seconds)
CACHE_TTL = 600

# HN Algolia API endpoint
HN_API_BASE = "https://hn.algolia.com/api/v1"

# Lock key to prevent cache stampede
LOCK_KEY = "tech:trending:lock"
LOCK_TTL = 30  # 30 seconds


def get_cache_key(source: str, limit: int) -> str:
    """Get Redis key for tech trending cache"""
    return f"tech:trending:{source}:{limit}"


def acquire_lock() -> bool:
    """Acquire distributed lock to prevent cache stampede"""
    if not redis_client:
        return True
    return redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL)


def release_lock():
    """Release distributed lock"""
    if redis_client:
        redis_client.delete(LOCK_KEY)


def translate_title_to_chinese(title: str) -> str:
    """
    Translate English title to Chinese using Gemini (if available)
    Falls back to original if translation fails
    """
    # Simple check: if title contains mostly Chinese characters, return as-is
    chinese_char_count = sum(1 for char in title if '\u4e00' <= char <= '\u9fff')
    if chinese_char_count > len(title) * 0.3:  # More than 30% Chinese chars
        return title
    
    # If Gemini is available, try to translate
    if GEMINI_API_KEY and GEMINI_AVAILABLE:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # Use gemini-1.5-flash or gemini-1.5-pro instead of gemini-pro
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                except:
                    model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""请将以下英文科技新闻标题翻译成中文，保留公司名和技术术语的英文（如 OpenAI、GPT、NVIDIA），只翻译其他部分：

标题：{title}

只返回翻译后的中文标题，不要其他文字。"""
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 100,
                }
            )
            
            translated = response.text.strip()
            # Remove quotes if present
            if translated.startswith('"') and translated.endswith('"'):
                translated = translated[1:-1]
            if translated.startswith("'") and translated.endswith("'"):
                translated = translated[1:-1]
            
            if translated and len(translated) > 0:
                return translated
        except Exception as e:
            print(f"Translation error for title '{title}': {e}")
    
    # Fallback: return original title (frontend will handle display)
    return title


def generate_tags(title: str, url: str = "") -> List[str]:
    """
    Generate deterministic tags based on title and URL keywords
    Rules are stable and deterministic (no randomness)
    Returns 2-3 tags max
    """
    tags = []
    title_lower = title.lower()
    url_lower = url.lower()
    combined_text = f"{title_lower} {url_lower}"
    
    # AI-related (highest priority)
    ai_keywords = ['openai', 'chatgpt', 'anthropic', 'claude', 'llama', 'model', 'ai', 'gpt', 'llm', 'gemini', 'machine learning', 'ml', 'deep learning', 'neural']
    if any(kw in combined_text for kw in ai_keywords):
        tags.append('AI')
    
    # Chips (semiconductor)
    chip_keywords = ['nvidia', 'cuda', 'gpu', 'chip', 'silicon', 'nvda', 'amd', 'intel', 'semiconductor', 'tsmc', 'qualcomm']
    if any(kw in combined_text for kw in chip_keywords):
        tags.append('芯片')
    
    # BigTech (major tech companies)
    bigtech_keywords = ['meta', 'google', 'apple', 'microsoft', 'amazon', 'tesla', 'facebook', 'netflix', 'uber', 'airbnb']
    if any(kw in combined_text for kw in bigtech_keywords):
        tags.append('大厂')
    
    # Career (job-related)
    career_keywords = ['layoffs', 'hiring', 'interview', 'career', 'job', 'salary', 'h1b', 'green card', 'immigration', 'resume', 'linkedin', 'pip', 'fired']
    if any(kw in combined_text for kw in career_keywords):
        tags.append('职场')
    
    # OpenSource
    opensource_keywords = ['open-source', 'opensource', 'github', 'repo', 'license', 'apache', 'mit license', 'gpl', 'agpl', 'contributor']
    if any(kw in combined_text for kw in opensource_keywords):
        tags.append('开源')
    
    # Security
    security_keywords = ['security', 'exploit', 'vuln', 'cve', 'hack', 'breach', 'vulnerability', 'cyber', 'ransomware', 'malware']
    if any(kw in combined_text for kw in security_keywords):
        tags.append('安全')
    
    # Infrastructure (lowest priority, catch-all for tech infra)
    infra_keywords = ['infra', 'kubernetes', 'postgres', 'redis', 'latency', 'aws', 'cloud', 'docker', 'devops', 'sre', 'database', 'scalability']
    if any(kw in combined_text for kw in infra_keywords):
        tags.append('基础设施')
    
    # Default to Tech if no tags matched
    if not tags:
        tags.append('科技')
    
    # Return max 2-3 tags (prioritize AI, Chips, BigTech, Career)
    priority_order = ['AI', '芯片', '大厂', '职场', '开源', '安全', '基础设施', '科技']
    sorted_tags = sorted(tags, key=lambda t: priority_order.index(t) if t in priority_order else 999)
    return sorted_tags[:3]


def generate_summary(title: str, url: str = "") -> Optional[str]:
    """
    Generate one-line summary from title
    Simple rule-based (no LLM)
    """
    # For MVP, just return None (optional field)
    # Future: could extract key info from title
    return None


def fetch_hn_stories(limit: int = 12) -> List[Dict]:
    """
    Fetch recent top stories from Hacker News using Algolia API
    Returns list of story dicts sorted by recent popularity
    """
    try:
        # Use search_by_date to get recent stories, then filter by points
        # This ensures we get recent news, not historical popular posts
        url = f"{HN_API_BASE}/search_by_date"
        params = {
            "tags": "story",
            "numericFilters": "points>10",  # Only stories with >10 points
            "hitsPerPage": limit * 2,  # Get more to filter by recency
            "page": 0
        }
        
        with httpx.Client(timeout=5.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            stories = []
            now = datetime.now(pytz.UTC)
            # Filter to only include stories from last 3 days
            cutoff_date = now - timedelta(days=3)
            
            for hit in data.get("hits", []):
                # Parse HN story
                story_id = hit.get("objectID", "")
                title = hit.get("title", "")
                url = hit.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                points = hit.get("points", 0)
                num_comments = hit.get("num_comments", 0)
                author = hit.get("author", "")
                created_at = hit.get("created_at", "")
                
                # Parse created_at (ISO format from Algolia)
                try:
                    if created_at:
                        # Algolia returns ISO format
                        created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    else:
                        created_dt = datetime.now(pytz.UTC)
                except:
                    created_dt = datetime.now(pytz.UTC)
                
                # Only include stories from last 3 days
                if created_dt < cutoff_date:
                    continue
                
                # Generate tags and summary
                tags = generate_tags(title, url)
                summary = generate_summary(title, url)
                
                # Translate title to Chinese if needed
                title_cn = translate_title_to_chinese(title)
                
                story = {
                    "id": f"hn_{story_id}",
                    "title": title,  # Original English title
                    "title_cn": title_cn,  # Chinese translation (may be same as title if already Chinese)
                    "url": url,
                    "score": points,
                    "comments": num_comments,
                    "author": author,
                    "createdAt": created_dt.isoformat(),
                    "tags": tags,
                    "summary": summary
                }
                
                stories.append(story)
                
                # Stop when we have enough recent stories
                if len(stories) >= limit:
                    break
            
            # Sort by score (descending) for final ordering
            stories.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            return stories[:limit]
            
    except httpx.TimeoutException:
        print("HN API timeout")
        return []
    except Exception as e:
        print(f"Error fetching HN stories: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_mock_tech_items() -> List[Dict]:
    """Return mock tech items as fallback"""
    return [
        {
            "id": "hn_mock_1",
            "title": "OpenAI releases GPT-5 with improved reasoning",
            "url": "https://example.com/gpt5",
            "score": 1234,
            "comments": 89,
            "author": "openai_team",
            "createdAt": datetime.now(pytz.UTC).isoformat(),
            "tags": ["AI", "BigTech"],
            "summary": None
        },
        {
            "id": "hn_mock_2",
            "title": "NVIDIA announces next-gen GPU architecture",
            "url": "https://example.com/nvidia",
            "score": 892,
            "comments": 156,
            "author": "nvidia_news",
            "createdAt": (datetime.now(pytz.UTC) - timedelta(hours=2)).isoformat(),
            "tags": ["Chips", "BigTech"],
            "summary": None
        },
        {
            "id": "hn_mock_3",
            "title": "AWS introduces new serverless compute option",
            "url": "https://example.com/aws",
            "score": 567,
            "comments": 78,
            "author": "aws_engineer",
            "createdAt": (datetime.now(pytz.UTC) - timedelta(hours=4)).isoformat(),
            "tags": ["Infra", "BigTech"],
            "summary": None
        }
    ]


def fetch_tech_trending(source: str = "hn", limit: int = 12) -> Dict:
    """
    Fetch trending tech news from specified source
    Currently supports: hn (Hacker News)
    
    Returns:
    {
        "source": "hn",
        "updatedAt": "ISO",
        "dataSource": "live|mock",
        "items": [...]
    }
    """
    cache_key = get_cache_key(source, limit)
    
    # Check cache first
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    # Acquire lock to prevent cache stampede
    if not acquire_lock():
        # If lock exists, return cached data if available
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except:
                    pass
        # If no cache, return mock immediately
        return {
            "source": source,
            "updatedAt": datetime.now(pytz.UTC).isoformat(),
            "dataSource": "mock",
            "items": get_mock_tech_items()[:limit]
        }
    
    try:
        items = []
        data_source = "live"
        
        if source == "hn":
            items = fetch_hn_stories(limit)
            if not items:
                # Fallback to mock if fetch fails
                items = get_mock_tech_items()[:limit]
                data_source = "mock"
        else:
            # Unknown source, return mock
            items = get_mock_tech_items()[:limit]
            data_source = "mock"
        
        # Sort items by score (descending) for stable ordering
        items.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Use consistent timestamp for the response
        updated_at = datetime.now(pytz.UTC)
        
        result = {
            "source": source,
            "updatedAt": updated_at.isoformat(),
            "dataSource": data_source,
            "stale": False,
            "ttlSeconds": CACHE_TTL,
            "items": items
        }
        
        # Cache the result
        if redis_client:
            redis_client.setex(
                cache_key,
                CACHE_TTL,
                json.dumps(result, default=str)
            )
        
        return result
        
    except Exception as e:
        print(f"Error in fetch_tech_trending: {e}")
        import traceback
        traceback.print_exc()
        # Return mock on any error
        updated_at = datetime.now(pytz.UTC)
        return {
            "source": source,
            "updatedAt": updated_at.isoformat(),
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": CACHE_TTL,
            "items": get_mock_tech_items()[:limit]
        }
    finally:
        release_lock()

