"""
Judgment Layer Service
Generates opinionated, filtered judgments for homepage sections using Gemini API
All judgments are cached and failure-safe
"""
import os
import redis
import json
import hashlib
from typing import Dict, Optional, List, Any
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

# Cache TTLs (in seconds)
CACHE_TTL_PORTFOLIO = 30 * 60  # 30 minutes
CACHE_TTL_MORTGAGE = 60 * 60  # 1 hour
CACHE_TTL_OFFER = 60 * 60  # 1 hour
CACHE_TTL_FOOD = 24 * 60 * 60  # 24 hours (places don't change often)
CACHE_TTL_ENTERTAINMENT = 6 * 60 * 60  # 6 hours


def get_cache_key(section_type: str, data_hash: str) -> str:
    """Generate cache key from section type and data hash"""
    return f"judgment:{section_type}:{data_hash}"


def generate_judgment_with_gemini(section_type: str, prompt: str, max_chars: int = 25) -> Optional[str]:
    """
    Generate judgment using Gemini API
    Returns None on failure (failure-safe)
    """
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return None
    
    try:
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
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Limit to max_chars
        if len(text) > max_chars:
            text = text[:max_chars - 3] + "..."
        
        return text
    except Exception as e:
        print(f"Error generating judgment for {section_type}: {e}")
        return None


def generate_portfolio_judgment(
    day_gain: float,
    day_gain_percent: float,
    top_movers: List[Dict],
    index_change: Optional[float] = None
) -> Optional[str]:
    """
    Generate judgment for portfolio section
    Question: "我今天的钱整体状态如何？"
    
    Returns: <= 25 Chinese characters
    Example: "今天是结构性波动，主要由 NVDA 拖累，非系统性下跌"
    """
    # Create data hash for caching
    data_str = f"{day_gain:.2f}:{day_gain_percent:.2f}:{index_change or 0:.2f}"
    if top_movers:
        movers_str = ",".join([f"{m.get('ticker', '')}:{m.get('day_gain_percent', 0):.2f}" for m in top_movers[:3]])
        data_str += f":{movers_str}"
    
    data_hash = hashlib.md5(data_str.encode()).hexdigest()[:16]
    cache_key = get_cache_key("portfolio", data_hash)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return cached
    
    # Build prompt
    movers_text = ""
    if top_movers:
        movers_list = []
        for m in top_movers[:3]:
            ticker = m.get('ticker', '')
            gain_pct = m.get('day_gain_percent', 0)
            movers_list.append(f"{ticker} {gain_pct:+.1f}%")
        movers_text = "主要波动: " + ", ".join(movers_list)
    
    index_text = ""
    if index_change is not None:
        index_text = f"大盘变化: {index_change:+.2f}%"
    
    prompt = f"""你是一个为湾区码农提供资产判断的助手。

今日涨跌: ${day_gain:+,.0f} ({day_gain_percent:+.2f}%)
{movers_text}
{index_text}

请用一句话（不超过25个中文字符）判断今天的资产整体状态。
要求：
1. 简洁有力，不超过25个中文字符
2. 说明是结构性波动还是系统性变化
3. 指出主要驱动因素（如某只股票拖累或推动）
4. 用中文回答

直接输出判断，不要包含其他文字："""
    
    judgment = generate_judgment_with_gemini("portfolio", prompt, max_chars=25)
    
    # Cache result
    if judgment and redis_client:
        redis_client.setex(cache_key, CACHE_TTL_PORTFOLIO, judgment)
    
    return judgment


def generate_mortgage_judgment(
    rate_30y: float,
    rate_7_1_arm: float,
    rate_trend: Optional[List[float]] = None
) -> Optional[str]:
    """
    Generate judgment for mortgage rates
    Question: "我现在该不该关心买房或 refi？"
    
    Returns: <= 25 Chinese characters
    Example: "利率连续横盘，短期 refi 价值不高"
    """
    # Create data hash
    trend_str = ""
    if rate_trend:
        trend_str = ",".join([f"{r:.2f}" for r in rate_trend[-7:]])  # Last 7 days
    
    data_str = f"{rate_30y:.2f}:{rate_7_1_arm:.2f}:{trend_str}"
    data_hash = hashlib.md5(data_str.encode()).hexdigest()[:16]
    cache_key = get_cache_key("mortgage", data_hash)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return cached
    
    # Build prompt
    trend_text = ""
    if rate_trend and len(rate_trend) >= 2:
        recent_change = rate_trend[-1] - rate_trend[-2]
        if len(rate_trend) >= 7:
            week_change = rate_trend[-1] - rate_trend[-7]
            trend_text = f"一周变化: {week_change:+.2f}%, 最近变化: {recent_change:+.2f}%"
        else:
            trend_text = f"最近变化: {recent_change:+.2f}%"
    
    prompt = f"""你是一个为湾区码农提供房贷建议的助手。

当前利率:
- 30年固定: {rate_30y:.2f}%
- 7/1 ARM: {rate_7_1_arm:.2f}%
{trend_text}

请用一句话（不超过25个中文字符）判断现在是否应该关心买房或refi。
要求：
1. 简洁有力，不超过25个中文字符
2. 说明利率趋势（上涨/下跌/横盘）
3. 给出建议（是否值得refi或关注买房）
4. 用中文回答

直接输出判断，不要包含其他文字："""
    
    judgment = generate_judgment_with_gemini("mortgage", prompt, max_chars=25)
    
    # Cache result
    if judgment and redis_client:
        redis_client.setex(cache_key, CACHE_TTL_MORTGAGE, judgment)
    
    return judgment


def generate_offer_market_judgment(
    recent_offers: List[Dict],
    layoff_news_count: int = 0,
    hiring_news_count: int = 0,
    market_sentiment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate market temperature and risk note for offers section
    Question: "市场现在给码农什么价？"
    
    Returns: {
        "temperature": "冷" | "正常" | "热",
        "risk_note": "<= 25 Chinese characters"
    }
    """
    # Create data hash
    offers_str = str(len(recent_offers))
    data_str = f"{offers_str}:{layoff_news_count}:{hiring_news_count}:{market_sentiment or ''}"
    data_hash = hashlib.md5(data_str.encode()).hexdigest()[:16]
    cache_key = get_cache_key("offer", data_hash)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except:
                pass
    
    # Build prompt
    offer_ranges = []
    for offer in recent_offers[:5]:  # Top 5 offers
        # Extract range if available (anonymized)
        title = offer.get('title', '')
        # Try to extract TC range (e.g., "300k-400k", "50万")
        import re
        tc_match = re.search(r'(\d+)[k万]', title, re.IGNORECASE)
        if tc_match:
            offer_ranges.append(tc_match.group(0))
    
    offers_text = f"最近offer数量: {len(recent_offers)}, 范围示例: {', '.join(offer_ranges[:3]) if offer_ranges else '无'}"
    news_text = f"裁员新闻: {layoff_news_count}条, 招聘新闻: {hiring_news_count}条"
    
    prompt = f"""你是一个为湾区码农提供就业市场判断的助手。

{offers_text}
{news_text}
市场情绪: {market_sentiment or '未知'}

请判断当前就业市场温度，并给出风险提示。
要求：
1. 温度: 冷/正常/热（只输出一个字）
2. 风险提示: 一句话，不超过25个中文字符
3. 用中文回答

格式：
温度：冷/正常/热
风险提示：[一句话]"""
    
    try:
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
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
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Parse response
            temperature = "正常"
            risk_note = "市场平稳"
            
            lines = text.split("\n")
            for line in lines:
                line = line.strip()
                if "温度" in line or "市场" in line:
                    if "冷" in line:
                        temperature = "冷"
                    elif "热" in line or "火" in line:
                        temperature = "热"
                    elif "正常" in line or "平稳" in line:
                        temperature = "正常"
                elif "风险" in line or "提示" in line:
                    # Extract text after colon
                    if "：" in line or ":" in line:
                        risk_note = line.split("：")[-1].split(":")[-1].strip()
                    else:
                        risk_note = line.strip()
                    # Limit to 25 chars
                    if len(risk_note) > 25:
                        risk_note = risk_note[:22] + "..."
            
            result = {
                "temperature": temperature,
                "risk_note": risk_note
            }
            
            # Cache result
            if redis_client:
                redis_client.setex(cache_key, CACHE_TTL_OFFER, json.dumps(result))
            
            return result
    except Exception as e:
        print(f"Error generating offer market judgment: {e}")
    
    # Fallback
    return {
        "temperature": "正常",
        "risk_note": "市场平稳"
    }


def generate_food_place_tag(place_name: str, cuisine_type: str, rating: Optional[float] = None) -> Optional[str]:
    """
    Generate short tag for food/boba place (OPTIONAL)
    Examples: "稳", "排队多", "适合带娃", "性价比高"
    
    Returns: <= 4 Chinese characters
    """
    # Create data hash
    data_str = f"{place_name}:{cuisine_type}:{rating or 0}"
    data_hash = hashlib.md5(data_str.encode()).hexdigest()[:16]
    cache_key = get_cache_key("food_tag", data_hash)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return cached
    
    # Build prompt
    prompt = f"""你是一个为湾区码农推荐餐厅的助手。

餐厅: {place_name}
类型: {cuisine_type}
评分: {rating or '未知'}

请用一个词（不超过4个中文字符）概括这个餐厅的特点。
例如: "稳", "排队多", "适合带娃", "性价比高", "环境好"
只输出一个词，不要其他文字："""
    
    tag = generate_judgment_with_gemini("food_tag", prompt, max_chars=4)
    
    # Cache result
    if tag and redis_client:
        redis_client.setex(cache_key, CACHE_TTL_FOOD, tag)
    
    return tag


def generate_entertainment_description(title: str, source: str = "") -> Optional[str]:
    """
    Generate short 1-line description for entertainment content (OPTIONAL)
    
    Returns: <= 30 Chinese characters
    """
    # Create data hash
    data_str = f"{title}:{source}"
    data_hash = hashlib.md5(data_str.encode()).hexdigest()[:16]
    cache_key = get_cache_key("entertainment", data_hash)
    
    # Check cache
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            return cached
    
    # Build prompt
    prompt = f"""你是一个为湾区码农推荐娱乐内容的助手。

标题: {title}
来源: {source}

请用一句话（不超过30个中文字符）描述这个内容，说明为什么值得看。
只输出描述，不要其他文字："""
    
    description = generate_judgment_with_gemini("entertainment", prompt, max_chars=30)
    
    # Cache result
    if description and redis_client:
        redis_client.setex(cache_key, CACHE_TTL_ENTERTAINMENT, description)
    
    return description
