"""
News Judgment Service - ONE-CALL Batch Processing
Uses Gemini to judge a batch of news items in a single call
"""
import os
import redis
import json
from typing import Dict, Optional, List
from datetime import datetime
import pytz

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Environment check: Disable Gemini in development/local
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in ["production", "prod"]
GEMINI_ENABLED = GEMINI_AVAILABLE and GEMINI_API_KEY and IS_PRODUCTION

# Daily call limiter
DAILY_CALL_LIMIT = int(os.getenv("GEMINI_DAILY_LIMIT", "20"))  # Max 20 calls per day (free-tier safe)
DAILY_CALL_COUNTER_KEY = "gemini_calls:{}"  # Format with date

# Cache TTL: 6 hours for batch judgment results
JUDGMENT_CACHE_TTL = 6 * 3600

# Hard blacklist keywords (EN + ZH)
BLACKLIST_KEYWORDS = [
    # English
    "protest", "protests", "riot", "war", "invasion", "gaza", "israel", "iran", 
    "ukraine", "palestine", "hamas", "terrorism", "election", "president", 
    "parliament", "coup",
    # Chinese
    "抗议", "游行", "战争", "入侵", "加沙", "以色列", "伊朗", "乌克兰", 
    "巴勒斯坦", "哈马斯", "恐怖", "选举", "总统", "议会", "政变"
]

# Exception keywords (allow if directly tied to tech)
EXCEPTION_KEYWORDS = [
    "export control", "chip ban", "antitrust", "sanction", "nvidia", "amd", 
    "asml", "semiconductor", "export restriction", "芯片", "出口管制", "反垄断"
]


def get_daily_call_count() -> int:
    """Get today's Gemini call count"""
    if not redis_client:
        return 0
    
    today = datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d")
    key = DAILY_CALL_COUNTER_KEY.format(today)
    count = redis_client.get(key)
    return int(count) if count else 0


def increment_daily_call_count() -> bool:
    """Increment today's call count. Returns True if under limit, False if exceeded."""
    if not redis_client:
        return False
    
    today = datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d")
    key = DAILY_CALL_COUNTER_KEY.format(today)
    
    # Increment and set expiry to end of day
    count = redis_client.incr(key)
    if count == 1:
        # Set expiry to end of day (24 hours from now)
        redis_client.expire(key, 86400)
    
    return count <= DAILY_CALL_LIMIT


def get_batch_judgment_cache_key() -> str:
    """Generate cache key for batch judgment (by date)"""
    today = datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d")
    return f"industry_news_judgment:{today}"


def prefilter_blacklist(items: List[Dict]) -> List[Dict]:
    """
    Hard pre-filter: Remove items with blacklist keywords
    Unless they contain exception keywords (tech-related)
    """
    filtered = []
    
    for item in items:
        title = (item.get("title") or "").lower()
        description = (item.get("description") or "").lower()
        text = f"{title} {description}"
        
        # Check if contains blacklist keyword
        has_blacklist = any(keyword.lower() in text for keyword in BLACKLIST_KEYWORDS)
        
        if has_blacklist:
            # Check if has exception keyword (tech-related)
            has_exception = any(keyword.lower() in text for keyword in EXCEPTION_KEYWORDS)
            if not has_exception:
                # Filter out
                continue
        
        filtered.append(item)
    
    return filtered


def judge_news_batch_with_gemini(items: List[Dict]) -> Optional[Dict]:
    """
    Use Gemini to judge a batch of news items in ONE call
    
    Input: List of news items (each with title, source, timestamp, url)
    Output: Dict with schema:
    {
      "date_local": "YYYY-MM-DD",
      "timezone": "America/Los_Angeles",
      "overall_brief_zh": "string",
      "shortage_reason": "string|null",
      "items": [...]
    }
    
    Returns None if Gemini unavailable, disabled, or error
    """
    if not GEMINI_ENABLED:
        print("Gemini disabled: Not in production environment or API key missing")
        return None
    
    # Check daily limit
    current_count = get_daily_call_count()
    if current_count >= DAILY_CALL_LIMIT:
        print(f"Gemini call skipped: Daily limit reached ({current_count}/{DAILY_CALL_LIMIT} calls)")
        return None
    
    if not increment_daily_call_count():
        print(f"Gemini call skipped: Daily limit exceeded after increment")
        return None
    
    try:
        print(f"Calling Gemini API for batch judgment of {len(items)} items (call #{get_daily_call_count()}/{DAILY_CALL_LIMIT})")
        genai.configure(api_key=GEMINI_API_KEY)
        # Use gemini-3-flash (primary), with fallbacks
        try:
            model = genai.GenerativeModel('gemini-3-flash')
        except:
            try:
                model = genai.GenerativeModel('gemini-2.5-pro')
            except:
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                except:
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                    except:
                        model = genai.GenerativeModel('gemini-pro')
        
        # Get local date
        local_tz = pytz.timezone("America/Los_Angeles")
        local_date = datetime.now(local_tz).strftime("%Y-%m-%d")
        
        # Format items for prompt
        items_text = []
        for i, item in enumerate(items[:30], 1):  # Limit to 30 items max
            title = item.get("title", "")
            source = item.get("source", "Unknown")
            url = item.get("url", "")
            timestamp = item.get("published_at")
            time_str = ""
            if timestamp:
                if isinstance(timestamp, datetime):
                    time_str = timestamp.strftime("%Y-%m-%d %H:%M")
                else:
                    time_str = str(timestamp)
            
            items_text.append(f"{i}. 标题: {title}\n   来源: {source}\n   时间: {time_str}\n   URL: {url}")
        
        prompt = f"""你是"湾区码农今日简报"的总编辑。你的目标不是全面报道，而是替湾区码农做判断：今天哪些科技/AI/大厂/股市/就业信息最值得看。

硬约束：
- 只关心：AI、芯片/半导体、云、Big Tech（NVDA/MSFT/META/GOOG/AMZN/AAPL/TSLA）、财报与指引、裁员/招聘、监管对科技股影响、重大产品/模型发布、并购。
- 过滤：世界政治/战争/抗议/社会新闻（除非直接影响科技股或大厂业务，例如出口管制/芯片禁令/反垄断重磅裁决）。
- 输出必须是 JSON 格式，严格符合以下 schema。
- 每条必须包含：summary_zh（1句）、why_it_matters_zh（1句）、tags（<=3）、relevance_score（0-100）、reason（简短解释你为何选它）、source_name、url、original_title。
- 必须返回 4-5 条；如果候选不足，宁可返回 3 条且说明 shortage_reason。
- 中文表达风格：像"朋友提醒你今天该盯啥"，短、直接、带行动性（对钱/工作有什么影响）。
- 不要输出英文标题作为主内容；英文只能放在 original_title 字段。

请分析以下{len(items_text)}条新闻：

{chr(10).join(items_text)}

输出格式（必须是有效的JSON，不要其他文字）：
{{
  "date_local": "{local_date}",
  "timezone": "America/Los_Angeles",
  "overall_brief_zh": "今天湾区码农该知道的3-5件事（一句话总结）",
  "shortage_reason": null,
  "items": [
    {{
      "id": "unique_id",
      "url": "原文链接",
      "source_name": "来源名称",
      "published_at": "YYYY-MM-DDTHH:MM:SS",
      "original_title": "原始英文标题",
      "summary_zh": "一句话中文摘要（≤28字）",
      "why_it_matters_zh": "一句话说明为什么重要（对钱/工作/技术的影响）",
      "tags": ["标签1", "标签2", "标签3"],
      "relevance_score": 85,
      "reason": "简短解释为何选这条"
    }}
  ]
}}

要求：
1. relevance_score: 0-100，只返回≥60的新闻
2. summary_zh: 像朋友提醒，短、直接、带行动性，≤28字
3. why_it_matters_zh: 说明对股票/职业/技术的影响，一句话
4. tags: 最多3个，从以下选择：AI, LLM, NVDA, MSFT, META, GOOG, AAPL, AMZN, TSLA, Chips, Cloud, Security, Earnings, Layoffs, Regulation, Startups
5. reason: 简短解释为何选这条
6. 必须返回4-5条，如果不足则返回3条并设置shortage_reason
7. 按relevance_score从高到低排序
8. overall_brief_zh: 一句话总结今天最重要的3-5件事

请直接输出JSON，不要其他文字："""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        print(f"Gemini response received: {len(text)} characters")
        
        # Parse JSON response
        try:
            # Try to extract JSON from response (might have markdown code blocks)
            json_text = text
            if "```json" in text:
                json_text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(json_text)
            
            # Validate schema
            if "items" not in result:
                print("Error: Gemini response missing 'items' field")
                return None
            
            items_count = len(result.get("items", []))
            print(f"Gemini batch judgment completed: {items_count} items returned")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error parsing Gemini JSON response: {e}")
            print(f"Response text (first 500 chars): {text[:500]}")
            return None
        except Exception as e:
            print(f"Error processing Gemini response: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    except Exception as e:
        print(f"Error judging news batch with Gemini: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_cached_or_judge_batch(items: List[Dict]) -> Dict:
    """
    Get cached batch judgment or generate new one using Gemini
    Returns dict with schema matching Gemini output
    
    In development/local: Always uses fallback, never calls Gemini
    """
    if not items:
        return {
            "date_local": datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d"),
            "timezone": "America/Los_Angeles",
            "overall_brief_zh": "",
            "shortage_reason": "无候选新闻",
            "items": []
        }
    
    cache_key = get_batch_judgment_cache_key()
    
    # Check cache
    if redis_client and cache_key:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                cached_data = json.loads(cached)
                print(f"Using cached batch judgment from {cache_key} ({len(cached_data.get('items', []))} items)")
                return cached_data
            except Exception as e:
                print(f"Error loading cached judgment: {e}")
    
    # Generate judgment
    judged_result = None
    
    if GEMINI_ENABLED:
        judged_result = judge_news_batch_with_gemini(items)
    
    # Fallback if Gemini unavailable, disabled, or failed
    if not judged_result:
        print("Using fallback judgment (Gemini unavailable/disabled/failed)")
        from app.services.news_summarizer import generate_summary_fallback
        from app.services.news_blacklist import extract_tags
        
        local_tz = pytz.timezone("America/Los_Angeles")
        local_date = datetime.now(local_tz).strftime("%Y-%m-%d")
        
        fallback_items = []
        for item in items[:5]:  # Limit to 5 items
            title = item.get("title", "")
            description = item.get("description", "")
            tags = extract_tags(title, description)
            summary_zh, why_it_matters_zh = generate_summary_fallback(title, description, tags)
            
            # Assign relevance score based on basic scoring
            relevance_score = 50
            if item.get("score", 0) >= 30:
                relevance_score = 65  # Above threshold
            
            if relevance_score >= 50:  # Lower threshold for fallback
                fallback_item = {
                    "id": item.get("url", "") or str(hash(title)),
                    "url": item.get("url", ""),
                    "source_name": item.get("source", "Unknown"),
                    "published_at": item.get("published_at").isoformat() if isinstance(item.get("published_at"), datetime) else str(item.get("published_at", "")),
                    "original_title": title,
                    "summary_zh": summary_zh,
                    "why_it_matters_zh": why_it_matters_zh,
                    "tags": tags[:3],
                    "relevance_score": relevance_score,
                    "reason": "基础相关性评分通过"
                }
                fallback_items.append(fallback_item)
        
        judged_result = {
            "date_local": local_date,
            "timezone": "America/Los_Angeles",
            "overall_brief_zh": f"今日科技新闻 {len(fallback_items)} 条",
            "shortage_reason": None if len(fallback_items) >= 4 else "候选新闻不足",
            "items": fallback_items
        }
    
    # Cache result (by date, TTL >= 6 hours)
    if redis_client and cache_key and judged_result:
        # Ensure UTF-8 encoding for Chinese characters
        redis_client.setex(cache_key, JUDGMENT_CACHE_TTL, json.dumps(judged_result, ensure_ascii=False))
        print(f"Cached batch judgment to {cache_key} (TTL: {JUDGMENT_CACHE_TTL}s, {len(judged_result.get('items', []))} items)")
    
    return judged_result
