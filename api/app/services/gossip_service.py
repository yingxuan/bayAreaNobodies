"""
Gossip discovery service for 北美华人八卦内容
Uses Google CSE to find gossip/discussion posts from 1point3acres, huaren.us, etc.
"""
import os
import re
import hashlib
from typing import List, Dict, Optional
from datetime import datetime
import pytz
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from app.services.google_search import fetch_multiple_pages, check_budget_exceeded
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Daily budget for gossip CSE (separate from main budget)
GOSSIP_CSE_DAILY_BUDGET = int(os.getenv("GOSSIP_CSE_DAILY_BUDGET", "50"))

# Source whitelist
GOSSIP_SOURCES = [
    "1point3acres.com",
    "huaren.us",
    "reddit.com",
]

# Query templates (老中八卦关键词)
GOSSIP_QUERIES = [
    # Chinese keywords (high priority)
    "site:1point3acres.com 八卦",
    "site:1point3acres.com 吃瓜",
    "site:1point3acres.com 围观",
    "site:1point3acres.com 吐槽",
    "site:1point3acres.com 奇葩",
    "site:1point3acres.com 翻车",
    "site:1point3acres.com 分手",
    "site:1point3acres.com 离婚",
    "site:1point3acres.com 出轨",
    "site:1point3acres.com 裁员",
    "site:1point3acres.com 被 PIP",
    "site:1point3acres.com 身份",
    "site:1point3acres.com 绿卡",
    "site:1point3acres.com H1B",
    "site:1point3acres.com 收入",
    "site:1point3acres.com 包裹",
    "site:1point3acres.com 年包",
    "site:1point3acres.com 学区",
    "site:1point3acres.com 私校",
    "site:1point3acres.com 带娃",
    "site:huaren.us 八卦",
    "site:huaren.us 吃瓜",
    "site:huaren.us 奇葩",
    "site:huaren.us 吐槽",
    "site:huaren.us 出轨",
    "site:huaren.us 离婚",
    "site:huaren.us 裁员",
    # English keywords (supporting)
    "site:reddit.com/r/ChineseAmerican",
    "site:reddit.com/r/cscareerquestions H1B layoff",
    "site:reddit.com 华人 离婚",
    "site:reddit.com 华人 layoff",
]


def get_gossip_usage_key() -> str:
    """Get Redis key for today's gossip CSE usage"""
    today = datetime.now().strftime("%Y%m%d")
    return f"gossip:cse:usage:{today}"


def check_gossip_budget_exceeded() -> bool:
    """Check if daily gossip CSE budget has been exceeded"""
    if not redis_client:
        return False
    usage_key = get_gossip_usage_key()
    current_usage = redis_client.get(usage_key)
    if current_usage is None:
        return False
    try:
        return int(current_usage) >= GOSSIP_CSE_DAILY_BUDGET
    except (ValueError, TypeError):
        return False


def increment_gossip_usage() -> int:
    """Increment daily gossip usage counter"""
    if not redis_client:
        return 0
    usage_key = get_gossip_usage_key()
    usage = redis_client.incr(usage_key)
    if usage == 1:
        redis_client.expire(usage_key, 90000)  # 25 hours
    return usage


def canonicalize_url(url: str) -> str:
    """Remove tracking parameters from URL"""
    if not url:
        return url
    
    parsed = urlparse(url)
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                       'gclid', 'fbclid', 'ref', 'source', 'campaign']
    
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}
    
    new_query = urlencode(cleaned_params, doseq=True)
    new_parsed = parsed._replace(query=new_query, fragment='')
    return urlunparse(new_parsed)


def extract_source_domain(url: str) -> Optional[str]:
    """Extract source domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None


def calculate_gossip_score(title: str, snippet: str, url: str) -> float:
    """
    Calculate 老中八卦度 score (0.0 to 1.0)
    Optimizes for "老中爱看、爱讨论、爱转发" content
    """
    text = f"{title} {snippet}".lower()
    score = 0.3  # Start at neutral
    
    # Boost: Chinese gossip keywords (+0.2)
    gossip_keywords_cn = ['八卦', '吃瓜', '围观', '吐槽', '奇葩', '翻车']
    if any(keyword in text for keyword in gossip_keywords_cn):
        score += 0.2
    
    # Boost: Life events (+0.15)
    life_keywords = ['分手', '离婚', '出轨', '结婚', '结婚', 'marriage', 'divorce', 'affair']
    if any(keyword in text for keyword in life_keywords):
        score += 0.15
    
    # Boost: Career/workplace (+0.15)
    career_keywords = ['裁员', '被 pip', 'layoff', 'fired', '被开', '被炒']
    if any(keyword in text for keyword in career_keywords):
        score += 0.15
    
    # Boost: Immigration/identity (+0.1)
    immigration_keywords = ['身份', '绿卡', 'h1b', 'green card', 'immigration', '公民']
    if any(keyword in text for keyword in immigration_keywords):
        score += 0.1
    
    # Boost: Income/salary (+0.1)
    income_keywords = ['收入', '包裹', '年包', 'salary', 'tc', 'total comp']
    if any(keyword in text for keyword in income_keywords):
        score += 0.1
    
    # Boost: Chinese/North America mentions (+0.1)
    location_keywords = ['华人', '湾区', '北美', 'chinese', 'bay area', 'seattle', 'nyc', '多伦多']
    if any(keyword in text for keyword in location_keywords):
        score += 0.1
    
    # Boost: Forum discussion style (+0.1)
    discussion_patterns = ['我朋友', '求建议', '怎么办', '求助', '分享', '朋友', '同事']
    if any(pattern in text for pattern in discussion_patterns):
        score += 0.1
    
    # Boost: Question format (+0.05)
    if '?' in title or '？' in title or title.startswith(('我', '朋友', '同事')):
        score += 0.05
    
    # Penalize: Celebrity-only gossip (-0.3)
    celebrity_keywords = ['明星', 'celebrity', 'actor', 'actress', '歌手', '网红']
    if any(keyword in text for keyword in celebrity_keywords):
        # Only penalize if it's ONLY about celebrities
        if not any(kw in text for kw in ['华人', 'chinese', '湾区', 'bay area']):
            score -= 0.3
    
    # Penalize: Generic news reporting (-0.2)
    news_keywords = ['报道', '新闻', 'news', 'report', 'breaking']
    if any(keyword in text for keyword in news_keywords) and '讨论' not in text:
        score -= 0.2
    
    # Penalize: Marketing/clickbait domains (-0.2)
    marketing_domains = ['weibo.com', 'toutiao.com', 'sina.com']
    source_domain = extract_source_domain(url)
    if source_domain in marketing_domains:
        score -= 0.2
    
    # Penalize: Very short content (-0.1)
    if len(snippet) < 50:
        score -= 0.1
    
    return max(0.0, min(score, 1.0))  # Clamp between 0.0 and 1.0


def detect_gossip_topic(title: str, snippet: str) -> Optional[str]:
    """Detect gossip topic category"""
    text = f"{title} {snippet}".lower()
    
    # 职场瓜
    if any(kw in text for kw in ['裁员', '被 pip', 'layoff', 'fired', '被开', '工作', '公司', '同事']):
        return '职场瓜'
    
    # 家庭瓜
    if any(kw in text for kw in ['带娃', '学区', '私校', '教育', '孩子', '娃']):
        return '家庭瓜'
    
    # 身份瓜
    if any(kw in text for kw in ['身份', '绿卡', 'h1b', 'green card', 'immigration', '公民']):
        return '身份瓜'
    
    # 感情瓜
    if any(kw in text for kw in ['分手', '离婚', '出轨', '结婚', 'marriage', 'divorce', 'affair']):
        return '感情瓜'
    
    return None


def search_and_store_gossip(db):
    """
    Search for gossip using CSE and store in database
    Returns (processed_count, skipped_count, quota_exceeded)
    """
    from app.models import Article
    from app.services.article_fetcher import normalize_url, compute_content_hash
    
    if check_gossip_budget_exceeded():
        print("WARNING: Daily gossip CSE budget exceeded. Skipping gossip search.")
        return (0, 0, True)
    
    processed = 0
    skipped = 0
    quota_exceeded = False
    
    for query in GOSSIP_QUERIES:
        if check_gossip_budget_exceeded():
            print(f"WARNING: Budget exceeded. Processed {processed} queries.")
            quota_exceeded = True
            skipped = len(GOSSIP_QUERIES) - processed
            break
        
        try:
            # Check budget before each query
            if check_gossip_budget_exceeded():
                quota_exceeded = True
                skipped = len(GOSSIP_QUERIES) - processed
                break
            
            # Search with date restriction (d7 for recent gossip)
            results = fetch_multiple_pages(
                query=query,
                site_domain=None,
                max_results=10,
                date_restrict="d7"
            )
            
            # Increment gossip usage counter
            if results:
                increment_gossip_usage()
            
            if not results:
                continue
            
            # Process each result
            for item in results:
                url = item.get("link", "")
                if not url:
                    continue
                
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                
                # Only process allowed sources
                source_domain = extract_source_domain(url)
                if not any(allowed in source_domain for allowed in ["1point3acres.com", "huaren.us", "reddit.com"]):
                    continue
                
                # Normalize URL
                normalized = normalize_url(url)
                
                # Check for duplicate
                existing = db.query(Article).filter(
                    Article.normalized_url == normalized
                ).first()
                
                if existing:
                    # Update gossip_score if needed
                    new_gossip_score = calculate_gossip_score(title, snippet, url)
                    if new_gossip_score > (existing.gossip_score or 0):
                        existing.gossip_score = new_gossip_score
                        existing.fetched_at = datetime.now(pytz.UTC)
                    continue
                
                # Check by content hash
                content_hash = compute_content_hash(title, normalized)
                duplicate = db.query(Article).filter(
                    Article.content_hash == content_hash
                ).first()
                
                if duplicate:
                    continue
                
                # Determine source_type
                if "1point3acres.com" in url:
                    source_type = "di_li"
                elif "huaren.us" in url:
                    source_type = "di_li"  # Treat as same category
                elif "reddit.com" in url:
                    source_type = "reddit"
                else:
                    source_type = "gossip"
                
                # Calculate gossip score
                gossip_score = calculate_gossip_score(title, snippet, url)
                
                # Detect topic
                topic = detect_gossip_topic(title, snippet)
                
                # Create article entry
                article = Article(
                    url=url,
                    normalized_url=normalized,
                    title=title,
                    cleaned_text=snippet[:5000],  # Limit size
                    content_hash=content_hash,
                    source_type=source_type,
                    platform="web",
                    summary=snippet[:500],
                    gossip_score=gossip_score,
                    fetched_at=datetime.now(pytz.UTC)
                )
                
                # Add topic to tags if detected
                if topic:
                    article.tags = f'["{topic}"]'
                
                db.add(article)
            
            processed += 1
            db.commit()
            
        except Exception as e:
            print(f"Error processing gossip query '{query}': {e}")
            db.rollback()
            continue
    
    return (processed, skipped, quota_exceeded)

