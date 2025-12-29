"""
Deals discovery service for 北美华人羊毛信息
Uses Google CSE to find bank/credit card/brokerage/life deals
"""
import os
import re
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pytz
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from app.services.google_search import search_google, fetch_multiple_pages, check_budget_exceeded, increment_usage
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

# Daily budget for deals CSE (separate from main budget)
DEALS_CSE_DAILY_BUDGET = int(os.getenv("DEALS_CSE_DAILY_BUDGET", "80"))

# Curated source list (老中友好优先)
DEAL_SOURCES = [
    # Financial (existing)
    "doctorofcredit.com",
    "1point3acres.com",
    "huaren.us",
    "slickdeals.net",
    "chase.com",
    "bankofamerica.com",
    "wellsfargo.com",
    "citibank.com",
    "usbank.com",
    "capitalone.com",
    # Food / Restaurant (new)
    "thekrazycouponlady.com",
    "hip2save.com",
    "brandeating.com",
    "mcdonalds.com",
    "chipotle.com",
    "tacobell.com",
    "wendys.com",
    # Retail / Family (new)
    "costco.com",
    "target.com",
    "walmart.com",
    "amazon.com",
]

# Query templates by category
QUERY_TEMPLATES = {
    "bank": [
        "site:doctorofcredit.com checking bonus",
        "site:doctorofcredit.com savings bonus",
        "site:doctorofcredit.com bank bonus",
        "site:1point3acres.com DP checking bonus",
        "site:1point3acres.com 开户 奖励 实测",
        "site:huaren.us 银行 开户 奖励",
        "site:slickdeals.net bank bonus",
        "(Chase OR \"Bank of America\" OR Citi OR \"Wells Fargo\") checking bonus \"Doctor of Credit\"",
        "checking bonus $200 $300 $500",
        "savings bonus $200 $300 $500",
    ],
    "card": [
        "site:doctorofcredit.com credit card welcome bonus",
        "site:doctorofcredit.com signup bonus",
        "site:1point3acres.com 信用卡 开卡 奖励",
        "site:huaren.us 信用卡 开卡 奖励",
        "site:slickdeals.net credit card bonus",
        "Chase Sapphire Preferred bonus",
        "Amex Platinum bonus",
        "credit card signup bonus $200 $300 $500",
        "开卡奖励 实测 亲测",
    ],
    "brokerage": [
        "site:doctorofcredit.com brokerage bonus",
        "site:doctorofcredit.com transfer bonus",
        "site:doctorofcredit.com ACAT bonus",
        "site:1point3acres.com 证券 开户 奖励",
        "site:huaren.us 券商 开户 奖励",
        "brokerage bonus $200 $500 $1000",
        "transfer bonus ACAT",
        "new account bonus brokerage",
    ],
    "life": [
        "site:1point3acres.com Costco deal",
        "site:1point3acres.com Sam's Club deal",
        "site:huaren.us 生活 优惠",
        "site:slickdeals.net grocery coupon",
        "site:slickdeals.net phone plan promo",
        "site:slickdeals.net internet promo",
        "dining coupon Bay Area",
        "Costco membership deal",
        "phone plan discount",
    ],
    "food_fast": [
        "site:doctorofcredit.com (doordash OR grubhub OR ubereats) promo",
        "site:doctorofcredit.com free food",
        "site:thekrazycouponlady.com fast food deal",
        "site:hip2save.com food deal",
        "(McDonald's OR Chipotle OR Taco Bell OR Wendy's) app deal",
        "site:brandeating.com promo",
        "fast food coupon app",
        "restaurant app discount",
    ],
    "retail_family": [
        "site:slickdeals.net (household OR detergent OR paper towels) deal",
        "site:slickdeals.net (clothing OR shoes) deal",
        "site:thekrazycouponlady.com (Target OR Walmart OR Costco) deal",
        "Amazon Subscribe and Save coupon",
        "site:costco.com coupon",
        "site:target.com deal",
        "site:walmart.com coupon",
        "household essentials deal",
    ],
}


def get_deals_usage_key() -> str:
    """Get Redis key for today's deals CSE usage"""
    today = datetime.now().strftime("%Y%m%d")
    return f"deals:cse:usage:{today}"


def check_deals_budget_exceeded() -> bool:
    """Check if daily deals CSE budget has been exceeded"""
    if not redis_client:
        return False
    usage_key = get_deals_usage_key()
    current_usage = redis_client.get(usage_key)
    if current_usage is None:
        return False
    try:
        return int(current_usage) >= DEALS_CSE_DAILY_BUDGET
    except (ValueError, TypeError):
        return False


def increment_deals_usage() -> int:
    """Increment daily deals usage counter"""
    if not redis_client:
        return 0
    usage_key = get_deals_usage_key()
    usage = redis_client.incr(usage_key)
    if usage == 1:
        redis_client.expire(usage_key, 90000)  # 25 hours
    return usage


def canonicalize_url(url: str) -> str:
    """Remove tracking parameters from URL"""
    if not url:
        return url
    
    parsed = urlparse(url)
    # Remove tracking params
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                       'gclid', 'fbclid', 'ref', 'source', 'campaign']
    
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}
    
    # Rebuild URL
    new_query = urlencode(cleaned_params, doseq=True)
    new_parsed = parsed._replace(query=new_query, fragment='')
    return urlunparse(new_parsed)


def compute_content_hash(title: str, url: str) -> str:
    """Compute hash for deduplication"""
    content = f"{title}:{url}".lower().strip()
    return hashlib.sha256(content.encode()).hexdigest()


def extract_source_domain(url: str) -> Optional[str]:
    """Extract source domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None


def calculate_chinese_friendliness_score(title: str, snippet: str, url: str) -> float:
    """
    Calculate 老中友好度 score (0.0 to 1.0)
    Optimizes for clarity, safety, and repeatability for Chinese families
    """
    text = f"{title} {snippet}".lower()
    score = 0.5  # Start at neutral
    
    # Boost: Official app or online order (+0.15)
    app_keywords = ['app', 'online', 'mobile app', 'official app', 'website', 'order online']
    if any(keyword in text for keyword in app_keywords):
        score += 0.15
    
    # Boost: Clear discount amount (+0.15)
    discount_patterns = [
        r'\$\d+ off', r'\d+% off', r'save \$\d+', r'\$\d+ discount',
        r'off', r'折扣', r'优惠', r'减'
    ]
    if any(re.search(pattern, text) for pattern in discount_patterns):
        score += 0.15
    
    # Boost: No minimum or simple minimum (+0.1)
    no_minimum_keywords = ['no minimum', 'no purchase required', 'free', '免费', '无门槛']
    simple_minimum_keywords = ['minimum', 'spend', 'purchase', '门槛']
    if any(keyword in text for keyword in no_minimum_keywords):
        score += 0.1
    elif any(keyword in text for keyword in simple_minimum_keywords):
        # Simple minimum (like "$10 minimum") is still good
        score += 0.05
    
    # Boost: New user or everyone eligible (+0.1)
    if 'new user' in text or 'everyone' in text or 'all customers' in text or '新用户' in text or '所有人' in text:
        score += 0.1
    
    # Boost: Common stores (Costco, Target, Walmart, Amazon) (+0.1)
    common_stores = ['costco', 'target', 'walmart', 'amazon', 'whole foods']
    if any(store in text for store in common_stores):
        score += 0.1
    
    # Penalize: YMMV mentions (-0.2)
    ymmv_keywords = ['ymmv', 'your mileage may vary', 'may not work', 'varies by location', 'manager approval']
    if any(keyword in text for keyword in ymmv_keywords):
        score -= 0.2
    
    # Penalize: In-store manager approval required (-0.15)
    if 'manager approval' in text or 'ask manager' in text or 'store manager' in text:
        score -= 0.15
    
    # Penalize: Complicated stacking language (-0.15)
    stacking_keywords = ['stack with', 'combine with', 'use together', 'multiple coupons', 'extreme couponing']
    if any(keyword in text for keyword in stacking_keywords):
        score -= 0.15
    
    # Penalize: Rebate-only or delayed payout (-0.1)
    rebate_keywords = ['rebate', 'mail-in rebate', 'delayed', 'takes weeks', 'refund later']
    if any(keyword in text for keyword in rebate_keywords):
        score -= 0.1
    
    # Penalize: Store hopping required (-0.1)
    if 'multiple stores' in text or 'store hopping' in text or 'visit multiple' in text:
        score -= 0.1
    
    return max(0.0, min(score, 1.0))  # Clamp between 0.0 and 1.0


def calculate_deal_score(title: str, snippet: str, url: str, published_at: Optional[datetime] = None) -> float:
    """
    Calculate relevance score for 北美华人适用性
    Returns score 0.0 to 1.0
    """
    text = f"{title} {snippet}".lower()
    score = 0.0
    
    # Bank mentions (+0.15)
    banks = ['chase', 'amex', 'american express', 'bank of america', 'boa', 'citi', 'citibank',
             'wells fargo', 'us bank', 'capital one', 'discover']
    if any(bank in text for bank in banks):
        score += 0.15
    
    # Bonus amounts (+0.2 for common amounts)
    bonus_amounts = ['$200', '$300', '$500', '$600', '$900', '$1000', '$1500']
    if any(amount in text for amount in bonus_amounts):
        score += 0.2
    
    # DP/实测/亲测 mentions (+0.15)
    dp_keywords = ['dp', '实测', '亲测', 'data point', 'success', '成功']
    if any(keyword in text for keyword in dp_keywords):
        score += 0.15
    
    # Direct deposit mentions (+0.1)
    dd_keywords = ['direct deposit', 'dd', '无dd', '免dd', 'no dd', 'no direct deposit']
    if any(keyword in text for keyword in dd_keywords):
        score += 0.1
    
    # ITIN/SSN mentions (+0.1)
    id_keywords = ['itin', 'ssn', 'social security', 'tax id']
    if any(keyword in text for keyword in id_keywords):
        score += 0.1
    
    # New customer mentions (+0.05)
    if 'new customer' in text or '新客户' in text:
        score += 0.05
    
    # In-branch/online mentions (+0.05)
    if 'in-branch' in text or 'online' in text or 'branch' in text:
        score += 0.05
    
    # Early closure clawback mentions (+0.05)
    if 'early closure' in text or 'clawback' in text or 'early termination' in text:
        score += 0.05
    
    # Penalize old content (if published_at available)
    if published_at:
        age_days = (datetime.now(pytz.UTC) - published_at).days
        if age_days > 60:
            score *= 0.5  # Halve score for old content
        elif age_days > 30:
            score *= 0.75
    
    # Penalize low-quality aggregator domains
    low_quality_domains = ['dealmoon.com', 'slickdeals.net']  # Less authoritative
    source_domain = extract_source_domain(url)
    if source_domain in low_quality_domains:
        score *= 0.8
    
    # Boost authoritative sources
    authoritative_domains = ['doctorofcredit.com', '1point3acres.com', 'huaren.us']
    if source_domain in authoritative_domains:
        score *= 1.2
    
    base_score = min(score, 1.0)  # Cap at 1.0
    
    return base_score  # Base score returned, chinese_friendliness calculated separately


def build_queries() -> List[Dict[str, str]]:
    """Build list of queries to run"""
    queries = []
    
    for category, templates in QUERY_TEMPLATES.items():
        for template in templates:
            # Set date restrictions: food_fast (d7), retail_family (d30), others as before
            if category == "food_fast":
                date_restrict = "d7"
            elif category in ["life", "retail_family"]:
                date_restrict = "d30"
            else:
                date_restrict = "d7"
            
            queries.append({
                "query": template,
                "category": category,
                "date_restrict": date_restrict
            })
    
    return queries


def search_and_store_deals(db, category_filter: Optional[str] = None):
    """
    Search for deals using CSE and store in database
    Returns (processed_count, skipped_count, quota_exceeded)
    """
    from app.models import Coupon
    from sqlalchemy.orm import Session
    
    if check_deals_budget_exceeded():
        print("WARNING: Daily deals CSE budget exceeded. Skipping deal search.")
        return (0, 0, True)
    
    queries = build_queries()
    if category_filter:
        queries = [q for q in queries if q["category"] == category_filter]
    
    processed = 0
    skipped = 0
    quota_exceeded = False
    
    for query_info in queries:
        if check_deals_budget_exceeded():
            print(f"WARNING: Budget exceeded. Processed {processed} queries.")
            quota_exceeded = True
            skipped = len(queries) - processed
            break
        
        query = query_info["query"]
        category = query_info["category"]
        date_restrict = query_info["date_restrict"]
        
        try:
            # Check budget before each query
            if check_deals_budget_exceeded():
                quota_exceeded = True
                skipped = len(queries) - processed
                break
            
            # Search with caching (handled by google_search)
            # Note: This uses the main CSE budget, but we track deals budget separately
            results = fetch_multiple_pages(
                query=query,
                site_domain=None,  # Let query handle site: operator
                max_results=10,  # Limit per query to save quota
                date_restrict=date_restrict
            )
            
            # Increment deals usage counter only if we got results (API calls were made)
            # This is approximate - we count each query as 1 usage even if it made multiple API calls
            if results:
                increment_deals_usage()
            
            if not results:
                continue
            
            # Check if we hit quota after search
            if check_deals_budget_exceeded():
                quota_exceeded = True
                skipped = len(queries) - processed
                break
            
            # Process each result
            for item in results:
                url = item.get("link", "")
                if not url:
                    continue
                
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                
                # Canonicalize URL for dedup
                canonical_url = canonicalize_url(url)
                
                # Check for duplicate
                existing = db.query(Coupon).filter(
                    Coupon.canonical_url == canonical_url
                ).first()
                
                if existing:
                    # Update score if needed
                    new_score = calculate_deal_score(title, snippet, url, existing.published_at)
                    if new_score > existing.score:
                        existing.score = new_score
                        existing.fetched_at = datetime.now(pytz.UTC)
                    continue
                
                # Check by content hash
                content_hash = compute_content_hash(title, canonical_url)
                duplicate = db.query(Coupon).filter(
                    Coupon.content_hash == content_hash
                ).first()
                
                if duplicate:
                    continue
                
                # Extract published date from snippet if possible
                published_at = None
                # Try to extract date from snippet (basic pattern matching)
                date_patterns = [
                    r'(\d{1,2}/\d{1,2}/\d{4})',
                    r'(\d{4}-\d{2}-\d{2})',
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, snippet)
                    if match:
                        try:
                            from dateutil import parser
                            published_at = parser.parse(match.group(1))
                            if published_at.tzinfo is None:
                                published_at = pytz.UTC.localize(published_at)
                        except:
                            pass
                        break
                
                # Calculate scores
                base_score = calculate_deal_score(title, snippet, url, published_at)
                chinese_friendliness_score = calculate_chinese_friendliness_score(title, snippet, url)
                
                # Final score: blend base relevance (70%) with Chinese friendliness (30%)
                # This prioritizes relevance but boosts deals that are 老中友好
                final_score = 0.7 * base_score + 0.3 * chinese_friendliness_score
                final_score = min(final_score, 1.0)  # Cap at 1.0
                
                # Extract source domain
                source = extract_source_domain(url)
                
                # Create coupon/deal entry
                coupon = Coupon(
                    title=title,
                    code=None,  # Will be extracted later if needed
                    source_url=url,
                    canonical_url=canonical_url,
                    content_hash=content_hash,
                    published_at=published_at,
                    score=final_score,  # Store blended final score
                    chinese_friendliness_score=chinese_friendliness_score,
                    source=source,
                    category=category,
                    terms=snippet[:1000],  # Limit length
                    confidence=final_score,  # Use final score as confidence
                    fetched_at=datetime.now(pytz.UTC)
                )
                
                db.add(coupon)
            
            processed += 1
            db.commit()
            
        except Exception as e:
            print(f"Error processing query '{query}': {e}")
            db.rollback()
            continue
    
    return (processed, skipped, quota_exceeded)

