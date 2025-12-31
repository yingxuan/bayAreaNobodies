"""
News Relevance Scoring for Bay Area Tech Workers
Scores news items based on relevance, freshness, and market impact
"""
from typing import Dict
from datetime import datetime
import pytz
from app.services.news_blacklist import is_big_tech_related, extract_tags, BIG_TECH_KEYWORDS

# Scoring weights
RELEVANCE_WEIGHT = 60
FRESHNESS_WEIGHT = 20
MARKET_IMPACT_WEIGHT = 20


def calculate_relevance_score(item: Dict) -> float:
    """
    Calculate relevance score (0-60)
    Based on keyword triggers and source trust
    """
    title = (item.get("title") or "").lower()
    description = (item.get("description") or "").lower()
    text = f"{title} {description}"
    source = (item.get("source") or "").lower()
    
    score = 0
    
    # Big tech company mentions (high weight)
    big_tech_companies = [
        "openai", "google", "meta", "microsoft", "nvidia", "apple", "amazon",
        "tesla", "anthropic", "xai"
    ]
    for company in big_tech_companies:
        if company in text:
            score += 8  # High relevance
            break
    
    # AI/LLM keywords
    ai_keywords = ["llm", "large language model", "gpt", "claude", "gemini",
                   "chatgpt", "agi", "neural network", "machine learning"]
    for keyword in ai_keywords:
        if keyword in text:
            score += 6
            break
    
    # Infrastructure keywords
    infra_keywords = ["gpu", "cuda", "datacenter", "cloud", "aws", "azure",
                     "semiconductor", "chip", "tsmc"]
    for keyword in infra_keywords:
        if keyword in text:
            score += 5
            break
    
    # Market/career keywords
    market_keywords = ["earnings", "guidance", "layoff", "hiring", "stock",
                      "sec", "doj", "antitrust", "regulation"]
    for keyword in market_keywords:
        if keyword in text:
            score += 7  # High impact
            break
    
    # Source trust bonus
    trusted_sources = ["techcrunch", "reuters", "bloomberg", "wsj", "theverge",
                      "arstechnica", "wired"]
    if any(trusted in source for trusted in trusted_sources):
        score += 5
    
    # Cap at 60
    return min(60, score)


def calculate_freshness_score(item: Dict) -> float:
    """
    Calculate freshness score (0-20)
    <24h = 20, 24-48h = 15, 48-72h = 10, >72h = 5
    """
    published_at = item.get("published_at")
    if not published_at:
        return 5
    
    if isinstance(published_at, str):
        from dateutil import parser
        published_at = parser.parse(published_at)
    
    if published_at.tzinfo is None:
        published_at = pytz.UTC.localize(published_at)
    
    now = datetime.now(pytz.UTC)
    age_hours = (now - published_at).total_seconds() / 3600
    
    if age_hours < 24:
        return 20
    elif age_hours < 48:
        return 15
    elif age_hours < 72:
        return 10
    else:
        return 5


def calculate_market_impact_score(item: Dict) -> float:
    """
    Calculate market impact score (0-20)
    Based on earnings, layoffs, antitrust, major funding, chips supply
    """
    title = (item.get("title") or "").lower()
    description = (item.get("description") or "").lower()
    text = f"{title} {description}"
    
    score = 0
    
    # High impact keywords
    high_impact = ["earnings", "guidance", "layoff", "antitrust", "lawsuit",
                   "sec", "doj", "ipo", "acquisition", "merger"]
    for keyword in high_impact:
        if keyword in text:
            score += 10
            break
    
    # Medium impact
    medium_impact = ["funding", "series a", "series b", "unicorn", "valuation",
                     "stock surge", "stock plunge", "market"]
    for keyword in medium_impact:
        if keyword in text:
            score += 5
            break
    
    # Chips supply chain
    if any(kw in text for kw in ["chip", "semiconductor", "tsmc", "supply chain"]):
        score += 7
    
    return min(20, score)


def score_news_item(item: Dict) -> Dict:
    """
    Calculate total score for a news item
    Returns item with added score and tags
    """
    relevance = calculate_relevance_score(item)
    freshness = calculate_freshness_score(item)
    market_impact = calculate_market_impact_score(item)
    
    total_score = relevance + freshness + market_impact
    
    # Extract tags
    tags = extract_tags(item.get("title", ""), item.get("description", ""))
    
    # Add score and tags to item
    item["score"] = total_score
    item["tags"] = tags
    item["relevance_score"] = relevance
    item["freshness_score"] = freshness
    item["market_impact_score"] = market_impact
    
    return item


def rank_news_items(items: list[Dict]) -> list[Dict]:
    """
    Rank news items by score (descending)
    Then by freshness as tie-breaker
    """
    return sorted(
        items,
        key=lambda x: (
            -x.get("score", 0),
            -x.get("freshness_score", 0),
            x.get("published_at", datetime.min)
        )
    )
