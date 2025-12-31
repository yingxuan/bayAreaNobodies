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
    
    ONE-CALL Gemini batch judgment pipeline:
    - Collects 30-60 raw candidates
    - Pre-filters hard blacklist (politics/war/protests)
    - Calls Gemini ONCE for batch judgment (or uses cache)
    - Returns 4-5 high-signal items in Chinese
    
    Returns:
    - overall_brief_zh: One-sentence summary of today's top items
    - items: 4-5 items (target=5, min=4)
    - Each item includes:
      - summary_zh: Chinese summary (<=28 chars, friend-reminder style)
      - why_it_matters_zh: Why it matters (stock/career/tech impact)
      - tags: Max 3 tags (AI, LLM, NVDA, etc.)
      - original_url: Link to original article
      - source: News source
      - time_ago: Relative time
      - published_at: ISO timestamp
      - reason: Why this item was selected
      - judged: true/false (indicates judgment pipeline)
    
    Cached by date (6 hours TTL). Sources include:
    - RSS feeds (TechCrunch, The Verge, Ars Technica, Reuters)
    - Hacker News (filtered for big tech)
    
    All items are:
    - Pre-filtered for hard blacklist (politics/war/protests)
    - Judged by Gemini in ONE batch call
    - Filtered for SV tech relevance
    - Summarized in Chinese (friend-reminder style)
    """
    items = aggregate_industry_news(target_count=limit, min_count=4)
    
    formatted_items = [format_industry_news_item(item) for item in items]
    
    # Extract overall_brief_zh from first item (if available)
    overall_brief_zh = ""
    if formatted_items and formatted_items[0].get("overall_brief_zh"):
        overall_brief_zh = formatted_items[0].get("overall_brief_zh")
        # Remove from individual items
        for item in formatted_items:
            item.pop("overall_brief_zh", None)
    
    return {
        "overall_brief_zh": overall_brief_zh,
        "items": formatted_items,
        "total": len(formatted_items),
        "target": limit,
        "min_count": 4,
        "max_count": 6
    }
