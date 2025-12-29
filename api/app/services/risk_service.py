"""
Risk Service - Generate daily reminders for Bay Area engineers
Uses Gemini AI to generate contextual reminders, with fallback to mock seeds
"""
import os
import json
import redis
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz

# Optional imports - handle gracefully if not installed
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Risk reminders will use mock data only.")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Cache TTL: 12 hours (43200 seconds)
CACHE_TTL = 43200

# Lock key to prevent cache stampede
LOCK_KEY = "risk:today:lock"
LOCK_TTL = 30  # 30 seconds

# Mock seed library (fallback when Gemini unavailable)
MOCK_SEEDS = [
    {
        "id": "seed-1099",
        "title": "检查是否已收到所有 1099 表格",
        "why": "1 月底是 1099 表格发放截止日期，缺失表格可能影响报税",
        "who": "有投资账户、银行利息或副业收入的湾区码农",
        "action": "检查邮箱和账户通知，确认已收到所有 1099 表格",
        "deadline": "2025-01-31",
        "severity": "high",
        "category": "tax"
    },
    {
        "id": "seed-wash-sale",
        "title": "Tax-loss harvesting 需注意 wash sale 规则",
        "why": "30 天内买卖相同或相似证券会触发 wash sale，损失不能抵税",
        "who": "正在进行 tax-loss harvesting 的投资者",
        "action": "检查最近 30 天的交易记录，避免重复买入相同证券",
        "deadline": None,
        "severity": "med",
        "category": "tax"
    },
    {
        "id": "seed-rsu-blackout",
        "title": "留意 RSU vesting 后的 blackout period",
        "why": "公司财报发布前后可能有交易限制期，影响 RSU 卖出时机",
        "who": "持有 RSU 且计划近期卖出的员工",
        "action": "查看公司内部通知，确认 blackout period 时间窗口",
        "deadline": None,
        "severity": "med",
        "category": "work"
    },
    {
        "id": "seed-401k-rollover",
        "title": "401(k) rollover 需在 60 天内完成",
        "why": "离职后 401(k) 转出超过 60 天未完成会触发税务罚款",
        "who": "最近离职或换工作，需要处理 401(k) 账户的人",
        "action": "联系新雇主或 IRA 提供商，尽快完成 rollover 流程",
        "deadline": None,
        "severity": "high",
        "category": "finance"
    },
    {
        "id": "seed-insurance-renewal",
        "title": "年度保险自动续费即将到期",
        "why": "车险、房险通常在年初自动续费，价格可能上涨",
        "who": "持有车险或房险的湾区居民",
        "action": "检查保险账单，对比其他保险公司报价，考虑是否更换",
        "deadline": None,
        "severity": "low",
        "category": "life"
    }
]


def get_cache_key(city: str, date_str: str) -> str:
    """Get Redis key for risk cache"""
    return f"risk:today:{city}:{date_str}"


def acquire_lock() -> bool:
    """Acquire distributed lock to prevent cache stampede"""
    if not redis_client:
        return True
    return redis_client.set(LOCK_KEY, "1", nx=True, ex=LOCK_TTL)


def release_lock():
    """Release distributed lock"""
    if redis_client:
        redis_client.delete(LOCK_KEY)


def get_daily_mock_seeds() -> List[Dict]:
    """Get 1-2 mock seeds based on day of year (deterministic rotation)"""
    today = datetime.now(pytz.UTC)
    day_of_year = today.timetuple().tm_yday
    seed1_index = day_of_year % len(MOCK_SEEDS)
    seed2_index = (day_of_year + len(MOCK_SEEDS) // 2) % len(MOCK_SEEDS)
    
    if seed1_index == seed2_index:
        return [MOCK_SEEDS[seed1_index]]
    return [MOCK_SEEDS[seed1_index], MOCK_SEEDS[seed2_index]]


def is_mostly_chinese(text: str) -> bool:
    """Check if text is mostly Chinese characters"""
    if not text:
        return False
    chinese_char_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    # Consider it Chinese if more than 50% are Chinese characters
    return chinese_char_count > len(text) * 0.5


def validate_risk_item(item: Dict) -> bool:
    """Validate risk item structure and content, including Chinese language check"""
    required_fields = ['id', 'title', 'why', 'who', 'action', 'severity', 'category']
    for field in required_fields:
        if field not in item:
            return False
    
    # Field length validation
    if len(item.get('title', '')) > 40:
        return False
    if len(item.get('why', '')) > 80:
        return False
    if len(item.get('who', '')) > 40:
        return False
    if len(item.get('action', '')) > 80:
        return False
    
    # Chinese language validation - reject if mostly English
    title = item.get('title', '')
    why = item.get('why', '')
    who = item.get('who', '')
    action = item.get('action', '')
    
    # If any field is mostly English (not Chinese), reject the item
    if not is_mostly_chinese(title) or not is_mostly_chinese(why) or not is_mostly_chinese(who) or not is_mostly_chinese(action):
        print(f"Rejecting risk item due to English content: title='{title[:30]}...'")
        return False
    
    # Severity validation
    if item.get('severity') not in ['low', 'med', 'high']:
        return False
    
    # Category validation
    if item.get('category') not in ['tax', 'finance', 'work', 'legal', 'life']:
        return False
    
    return True


def generate_risk_with_gemini(city: str, date_str: str) -> Optional[List[Dict]]:
    """Generate risk items using Gemini AI"""
    if not GEMINI_API_KEY or not GEMINI_AVAILABLE:
        return None
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        system_prompt = """你是生活与合规提醒助手。只能提供面向大众的通用提醒，不提供个性化税务/投资/法律建议。输出必须是严格 JSON，不要 markdown，不要多余文字。最多 3 条。**所有内容必须使用中文，禁止使用英文句子。**"""
        
        user_prompt = f"""今天是 {date_str}，地区：湾区 {city}（California）。
请给湾区码农今天应该注意的 1–3 件事。
偏好：报税节点、tax-loss harvesting 的通用注意事项、RSU/401k/保险/合规。
每条必须包含 title/why/who/action/deadline/severity/category。

**重要要求：**
1. 所有字段（title/why/who/action）必须使用中文
2. 禁止输出英文句子
3. 公司名和技术术语可以保留英文（如 OpenAI、GPT、NVIDIA），但解释性文字必须是中文
4. 不要给个性化建议，不要要求隐私信息

输出格式（严格 JSON 数组，所有文字字段必须是中文）：
[
  {{
    "id": "unique-id",
    "title": "标题（≤40字，必须是中文）",
    "why": "事实背景（≤80字，必须是中文）",
    "who": "适用人群（≤40字，必须是中文）",
    "action": "可执行行动（≤80字，必须是中文）",
    "deadline": "YYYY-MM-DD 或 null",
    "severity": "low|med|high",
    "category": "tax|finance|work|legal|life"
  }}
]"""
        
        # Call Gemini with timeout
        response = model.generate_content(
            f"{system_prompt}\n\n{user_prompt}",
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1000,
            }
        )
        
        # Parse JSON from response
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse JSON
        items = json.loads(text)
        
        if not isinstance(items, list):
            return None
        
        # Validate and filter items
        valid_items = []
        for item in items[:3]:  # Max 3 items
            if validate_risk_item(item):
                valid_items.append(item)
        
        return valid_items if valid_items else None
        
    except json.JSONDecodeError as e:
        print(f"Gemini JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


def fetch_risk_today(city: str = "cupertino") -> Dict:
    """
    Fetch today's risk reminders
    Returns:
    {
        "updatedAt": "ISO",
        "dataSource": "gemini|cache|mock",
        "stale": bool,
        "ttlSeconds": int,
        "items": [...],
        "disclaimer": str
    }
    """
    today = datetime.now(pytz.UTC)
    date_str = today.strftime("%Y-%m-%d")
    cache_key = get_cache_key(city, date_str)
    
    # Check cache first
    if redis_client:
        cached = redis_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                # Check if cache is still valid
                cache_time = datetime.fromisoformat(data.get('updatedAt', '').replace('Z', '+00:00'))
                age_seconds = (today - cache_time).total_seconds()
                if age_seconds < CACHE_TTL:
                    return {
                        **data,
                        "stale": False,
                        "dataSource": "cache"
                    }
                else:
                    # Cache expired but can use as fallback
                    return {
                        **data,
                        "stale": True,
                        "dataSource": "cache"
                    }
            except:
                pass
    
    # Acquire lock to prevent cache stampede
    if not acquire_lock():
        # If lock exists, try to get last known good from cache
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                try:
                    data = json.loads(cached)
                    return {
                        **data,
                        "stale": True,
                        "dataSource": "cache"
                    }
                except:
                    pass
        # Fallback to mock
        return {
            "updatedAt": today.isoformat(),
            "dataSource": "mock",
            "stale": False,
            "ttlSeconds": CACHE_TTL,
            "items": get_daily_mock_seeds(),
            "disclaimer": "本信息仅供参考，不构成税务、投资或法律建议。请咨询专业人士获取个性化建议。"
        }
    
    try:
        items = None
        data_source = "mock"
        
        # Try Gemini first
        items = generate_risk_with_gemini(city, date_str)
        if items:
            data_source = "gemini"
        else:
            # Fallback to mock seeds
            items = get_daily_mock_seeds()
            data_source = "mock"
        
        result = {
            "updatedAt": today.isoformat(),
            "dataSource": data_source,
            "stale": False,
            "ttlSeconds": CACHE_TTL,
            "items": items,
            "disclaimer": "本信息仅供参考，不构成税务、投资或法律建议。请咨询专业人士获取个性化建议。"
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
        print(f"Error in fetch_risk_today: {e}")
        import traceback
        traceback.print_exc()
        # Final fallback to mock
        return {
            "updatedAt": today.isoformat(),
            "dataSource": "mock",
            "stale": True,
            "ttlSeconds": CACHE_TTL,
            "items": get_daily_mock_seeds(),
            "disclaimer": "本信息仅供参考，不构成税务、投资或法律建议。请咨询专业人士获取个性化建议。"
        }
    finally:
        release_lock()

