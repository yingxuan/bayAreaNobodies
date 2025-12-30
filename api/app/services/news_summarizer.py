"""
Chinese News Summarization Service
Generates summary_zh and why_it_matters_zh using Gemini API with caching
"""
import os
import redis
import json
import hashlib
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import pytz

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 6 hours for summaries
SUMMARY_CACHE_TTL = 6 * 3600


def get_cache_key(title: str, url: str) -> str:
    """Generate cache key from title and URL"""
    content = f"{title}:{url}".lower().strip()
    hash_val = hashlib.md5(content.encode()).hexdigest()[:16]
    return f"news_summary:{hash_val}"


def generate_summary_with_gemini(title: str, description: str = "", url: str = "") -> Optional[Tuple[str, str]]:
    """
    Generate Chinese summary and why_it_matters using Gemini API
    Returns (summary_zh, why_it_matters_zh) or None
    """
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return None
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""你是一个为湾区码农提供科技新闻摘要的助手。

新闻标题: {title}
新闻描述: {description[:200] if description else "无"}

请用中文回答，格式如下：

摘要（一句话，不超过28字）：
[一句话总结]

为什么重要（一句话，聚焦股票/职业/技术趋势）：
[为什么重要]

要求：
1. 摘要要简洁有力，不超过28个中文字符
2. "为什么重要"要说明对股票、职业发展或技术趋势的影响
3. 用中文回答，不要包含英文标题
4. 如果新闻不相关，返回"不相关"

请直接输出，格式：
摘要：
为什么重要："""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Parse response
        summary_zh = ""
        why_it_matters_zh = ""
        
        lines = text.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "摘要" in line or "总结" in line:
                current_section = "summary"
                # Extract text after colon
                if "：" in line or ":" in line:
                    summary_zh = line.split("：")[-1].split(":")[-1].strip()
            elif "为什么重要" in line or "重要性" in line:
                current_section = "why"
                if "：" in line or ":" in line:
                    why_it_matters_zh = line.split("：")[-1].split(":")[-1].strip()
            elif current_section == "summary" and not summary_zh:
                summary_zh = line.strip()
            elif current_section == "why" and not why_it_matters_zh:
                why_it_matters_zh = line.strip()
        
        # Fallback: if parsing failed, try to extract from full text
        if not summary_zh or not why_it_matters_zh:
            if "不相关" in text:
                return None
            # Try to split by common patterns
            parts = text.split("为什么重要")
            if len(parts) >= 2:
                summary_zh = parts[0].replace("摘要", "").replace("：", "").replace(":", "").strip()
                why_it_matters_zh = parts[1].replace("：", "").replace(":", "").strip()
        
        # Clean up
        summary_zh = summary_zh.strip().strip("：").strip(":").strip()
        why_it_matters_zh = why_it_matters_zh.strip().strip("：").strip(":").strip()
        
        if summary_zh and why_it_matters_zh and len(summary_zh) > 0 and len(why_it_matters_zh) > 0:
            # Limit summary to 28 chars
            if len(summary_zh) > 28:
                summary_zh = summary_zh[:25] + "..."
            return (summary_zh, why_it_matters_zh)
        
        return None
        
    except Exception as e:
        print(f"Error generating summary with Gemini: {e}")
        return None


def generate_summary_fallback(title: str, description: str = "", tags: list = None) -> Tuple[str, str]:
    """
    Fallback rule-based summary generation
    Uses simple translation dictionary and template-based why_it_matters
    """
    # Simple keyword-based translation (minimal dictionary)
    translations = {
        "openai": "OpenAI",
        "google": "谷歌",
        "meta": "Meta",
        "microsoft": "微软",
        "nvidia": "英伟达",
        "apple": "苹果",
        "amazon": "亚马逊",
        "tesla": "特斯拉",
        "ai": "AI",
        "llm": "大语言模型",
        "earnings": "财报",
        "layoff": "裁员",
        "hiring": "招聘",
        "stock": "股票",
        "chip": "芯片",
        "cloud": "云服务",
    }
    
    # Generate simple summary (use title with translations)
    summary_zh = title
    for en, zh in translations.items():
        if en.lower() in title.lower():
            summary_zh = summary_zh.replace(en, zh)
    
    # Generate why_it_matters from tags
    why_it_matters_zh = "值得关注"
    if tags:
        tag_impacts = {
            "AI": "AI技术趋势",
            "LLM": "大模型发展",
            "NVDA": "英伟达股价",
            "MSFT": "微软业务",
            "META": "Meta动态",
            "GOOG": "谷歌业务",
            "AAPL": "苹果动态",
            "Earnings": "财报影响",
            "Layoffs": "就业市场",
            "Regulation": "监管影响",
        }
        for tag in tags[:1]:  # Use first tag
            if tag in tag_impacts:
                why_it_matters_zh = f"关注{tag_impacts[tag]}"
                break
    
    return (summary_zh[:28], why_it_matters_zh)


def get_or_generate_summary(item: Dict) -> Dict:
    """
    Get cached summary or generate new one
    Adds summary_zh and why_it_matters_zh to item
    """
    title = item.get("title", "")
    description = item.get("description", "")
    url = item.get("url", "")
    tags = item.get("tags", [])
    
    cache_key = get_cache_key(title, url)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                cached_data = json.loads(cached)
                item["summary_zh"] = cached_data.get("summary_zh")
                item["why_it_matters_zh"] = cached_data.get("why_it_matters_zh")
                return item
            except:
                pass
    
    # Generate summary
    summary_result = None
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        summary_result = generate_summary_with_gemini(title, description, url)
    
    # Fallback to rule-based
    if not summary_result:
        summary_zh, why_it_matters_zh = generate_summary_fallback(title, description, tags)
    else:
        summary_zh, why_it_matters_zh = summary_result
    
    # Cache result
    if redis_client and summary_zh and why_it_matters_zh:
        cache_data = {
            "summary_zh": summary_zh,
            "why_it_matters_zh": why_it_matters_zh
        }
        redis_client.setex(cache_key, SUMMARY_CACHE_TTL, json.dumps(cache_data))
    
    item["summary_zh"] = summary_zh
    item["why_it_matters_zh"] = why_it_matters_zh
    
    return item
