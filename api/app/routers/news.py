"""
Industry News API endpoints
Returns curated Chinese-first news for Bay Area tech workers
"""
from fastapi import APIRouter, Query
from app.services.industry_news_service import aggregate_industry_news, format_industry_news_item
from typing import List, Dict

router = APIRouter()


@router.get("/industry")
def get_industry_news(
    limit: int = Query(default=5, ge=4, le=6, description="Number of items (target 5, min 4, max 6)")
) -> Dict:
    """
    Get curated industry news for Bay Area tech workers
    
    Returns:
    - 4-6 items (target=5)
    - Each item includes:
      - summary_zh: Chinese summary (<=28 chars)
      - why_it_matters_zh: Why it matters (stock/career/tech impact)
      - tags: Max 3 tags (AI, LLM, NVDA, etc.)
      - original_url: Link to original article
      - source: News source
      - time_ago: Relative time
      - published_at: ISO timestamp
    
    Cached for 10 minutes. Sources include:
    - RSS feeds (TechCrunch, The Verge, Ars Technica, Reuters)
    - Hacker News (filtered for big tech)
    
    All items are:
    - Filtered for relevance (big tech, AI, markets, career)
    - Scored and ranked
    - Summarized in Chinese
    - Deduplicated
    """
    items = aggregate_industry_news(target_count=limit, min_count=4)
    
    formatted_items = [format_industry_news_item(item) for item in items]
    
    return {
        "items": formatted_items,
        "total": len(formatted_items),
        "target": limit,
        "min_count": 4,
        "max_count": 6
    }
