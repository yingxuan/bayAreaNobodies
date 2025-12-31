# Industry News Section Refactor - Summary

## Task
Refactor ONLY the "行业新闻 / 今日热点" section to use Gemini judgment instead of raw news rendering.

## Changes Made

### 1. New Service: `api/app/services/news_judgment_service.py`
Created a new service that uses Gemini to process each news item:

**Functions:**
- `judge_news_item_with_gemini()`: Calls Gemini API to generate:
  - `summary_zh`: 1 Chinese sentence summarizing the news (≤28 chars)
  - `why_it_matters_zh`: 1 Chinese sentence explaining impact (money/career/AI/big tech)
  - `relevance_score`: Number 0-100

- `get_or_judge_news_item()`: Gets cached judgment or generates new one
  - Caches by URL (TTL ≥ 1 hour)
  - Filters out items with `relevance_score < 60`
  - Returns None if item should be filtered

- `filter_politics_war_protests()`: Explicitly filters out:
  - Politics (election, president, congress, etc.)
  - War (war, conflict, invasion, attack, etc.)
  - Protests (protest, demonstration, rally, etc.)

**Gemini Prompt:**
The service sends a structured prompt asking Gemini to:
1. Rate relevance (0-100, with <60 for politics/war/protests)
2. Generate Chinese summary (≤28 chars)
3. Explain why it matters (focus on stock/career/tech impact)

### 2. Updated: `api/app/services/industry_news_service.py`

**Changes:**
- Added import: `from app.services.news_judgment_service import get_or_judge_news_item, filter_politics_war_protests`

- Modified `aggregate_industry_news()` function:
  - After deduplication and basic scoring
  - **NEW STEP**: Process each item with Gemini judgment
    - Explicitly filter politics/war/protests
    - Call `get_or_judge_news_item()` for each item
    - Items with `relevance_score < 60` are filtered out
    - Limit to max 5 items
  - Only items that pass Gemini judgment are returned

- Updated `format_industry_news_item()`:
  - Now includes original `title` (English) for optional display
  - Uses `relevance_score` from Gemini instead of basic score

**Processing Flow:**
```
1. Fetch raw news (RSS + HN)
2. Deduplicate
3. Basic relevance scoring (min_score=30)
4. **NEW: Gemini Judgment Step**
   - Filter politics/war/protests explicitly
   - Call Gemini for each item
   - Filter relevance_score < 60
   - Limit to 5 items
5. Return judged items
```

### 3. Updated: `web/app/components/home/TechNewsList.tsx`

**Changes:**
- Updated empty state message: "今天没有重要行业新闻" (instead of "今天科技新闻较少，稍后再试")
- Added `title` field to `NewsItem` type (optional, for original English title)
- Added display of original English title (very small, hidden by default, shown on hover):
  ```tsx
  {item.title && (
    <p className="text-[10px] text-gray-400 line-clamp-1 mb-0.5 opacity-0 hover:opacity-100 transition-opacity">
      {item.title}
    </p>
  )}
  ```

## Filtering Rules

1. **Relevance Score**: Items with `relevance_score < 60` are filtered out
2. **Explicit Filters**: Politics, war, and protests are explicitly filtered
3. **Max Items**: Maximum 5 items are returned
4. **Min Items**: If fewer than 4 items survive filtering, frontend shows empty state

## Caching

- **Gemini Results**: Cached by URL (TTL = 1 hour)
- **Cache Key**: `news_judgment:{url_hash}`
- **Cache Format**: JSON with `relevance_score`, `summary_zh`, `why_it_matters_zh`

## Gemini Usage Confirmation

**Gemini is called in:**
- `news_judgment_service.py` → `judge_news_item_with_gemini()`
- Called for each news item in `industry_news_service.py` → `aggregate_industry_news()`

**How to verify Gemini is being called:**
1. Check API logs for "Error judging news item with Gemini" or successful calls
2. Check Redis cache keys: `news_judgment:*`
3. Check API response: Items should have `relevance_score`, `summary_zh`, `why_it_matters_zh`

## Files Modified

1. ✅ `api/app/services/news_judgment_service.py` (NEW FILE)
2. ✅ `api/app/services/industry_news_service.py` (MODIFIED)
3. ✅ `web/app/components/home/TechNewsList.tsx` (MODIFIED)

## Testing

To test:
1. Call `/api/news/industry?limit=5`
2. Check response items have:
   - `summary_zh` (Chinese summary)
   - `why_it_matters_zh` (Why it matters)
   - `relevance_score` (0-100)
   - `title` (Original English title)
3. Verify items with `relevance_score < 60` are filtered out
4. Verify politics/war/protests are filtered out
5. Verify max 5 items returned

## Notes

- Gemini API key must be set in environment: `GEMINI_API_KEY`
- If Gemini is unavailable, items will be filtered out (no fallback)
- Caching prevents repeated Gemini calls for same URLs
- Frontend shows empty state if < 3 items (or 0 items)
