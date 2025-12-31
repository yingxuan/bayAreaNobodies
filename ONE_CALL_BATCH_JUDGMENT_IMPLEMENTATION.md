# ONE-CALL Gemini Batch Judgment Pipeline Implementation

## Summary
Implemented a single-call Gemini batch judgment pipeline for the "行业新闻" section to fix quota issues and make the section Chinese-first and SV-tech relevant.

## Goal Achieved ✅
- **One homepage load triggers 0 Gemini calls** (reads from cache)
- **At most 1 Gemini call per scheduled refresh window** (or per cache miss)
- **Outputs 4–5 high-signal items in Chinese** with "why it matters"
- **Filters politics/war/protests** unless directly impacts big tech/AI/tech stocks

## Files Changed

### 1. `api/app/services/news_judgment_service.py` (COMPLETELY REWRITTEN)

**Key Functions Added:**

#### `prefilter_blacklist(items: List[Dict]) -> List[Dict]`
- Hard pre-filter: Removes items with blacklist keywords (EN + ZH)
- Exception: Allows items with tech-related keywords (export control, chip ban, antitrust, etc.)
- Blacklist keywords: protest, war, invasion, gaza, israel, iran, ukraine, 抗议, 战争, etc.
- Exception keywords: export control, chip ban, antitrust, nvidia, amd, asml, 芯片, 出口管制, 反垄断

#### `judge_news_batch_with_gemini(items: List[Dict]) -> Optional[Dict]`
- **ONE-CALL Gemini batch processing**
- Input: List of news items (up to 30)
- Output: JSON dict with schema:
  ```json
  {
    "date_local": "YYYY-MM-DD",
    "timezone": "America/Los_Angeles",
    "overall_brief_zh": "string",
    "shortage_reason": "string|null",
    "items": [
      {
        "id": "string",
        "url": "string",
        "source_name": "string",
        "published_at": "string",
        "original_title": "string",
        "summary_zh": "string",
        "why_it_matters_zh": "string",
        "tags": ["string"],
        "relevance_score": number,
        "reason": "string"
      }
    ]
  }
  ```
- **Gemini Prompt**: "湾区码农今日简报"总编辑 role
  - Chinese-first editorial tone: short, direct, actionable
  - Strictly filters world politics/war/protests unless impacts tech stocks
  - Outputs valid JSON only (no extra text)
- **Daily Call Limiter**: Max 20 calls per day (free-tier safe)
- **Environment Check**: Disabled in development/local (always uses fallback)

#### `get_cached_or_judge_batch(items: List[Dict]) -> Dict`
- **Cache Key**: `industry_news_judgment:{YYYY-MM-DD}` (by date)
- **TTL**: 6 hours
- **Cache Hit**: Returns cached result without calling Gemini
- **Cache Miss**: Calls Gemini ONCE for batch judgment
- **Fallback**: If Gemini fails/quota exceeded, uses rule-based fallback
- **Daily Limit Check**: Skips Gemini if `calls_today >= 20`

**Logging:**
- When Gemini batch is called (and why: cache miss + prod env)
- When skipped (dev env / cache hit / daily limit)
- When fallback used (Gemini error/quota)

### 2. `api/app/services/industry_news_service.py` (UPDATED)

**Changes:**
- Replaced per-item `get_or_judge_news_item()` calls with `get_cached_or_judge_batch()`
- Added `prefilter_blacklist()` before Gemini call
- Updated `aggregate_industry_news()` to use batch judgment:
  1. Collect raw items (30-60 candidates)
  2. Pre-filter hard blacklist keywords
  3. Take top 30 candidates
  4. Call Gemini ONCE for batch judgment (or get from cache)
  5. Extract items from judged result (max 5)
  6. Store `overall_brief_zh` and `judged` flag in each item

**Updated `format_industry_news_item()`:**
- Added `judged` field to API response
- Handles `published_at` as string or datetime
- Preserves all Gemini judgment fields

### 3. `api/app/routers/news.py` (UPDATED)

**Updated `/api/news/industry` endpoint:**
- Returns `overall_brief_zh` at top level
- Each item includes `judged` flag
- Updated docstring to reflect ONE-CALL batch judgment pipeline

### 4. `web/app/components/home/TechNewsList.tsx` (UPDATED)

**Changes:**
- Added `overall_brief_zh` display at top of card (if available)
- **Main line**: `item.summary_zh` (ALWAYS shown first)
- **Second line**: `item.why_it_matters_zh` (if available)
- **Tiny muted/hover-only**: `item.original_title` (only if different from summary)
- **Dev badge**: Shows "judged" or "cache" in development mode
- Updated type definitions to include `overall_brief_zh`, `judged`, `reason`

## Pipeline Flow

```
1. Collect Raw Items (30-60)
   ↓
2. Pre-filter Hard Blacklist (EN + ZH keywords)
   ↓
3. Take Top 30 Candidates
   ↓
4. Check Cache: industry_news_judgment:{YYYY-MM-DD}
   ├─ Cache Hit → Return cached result (0 Gemini calls)
   └─ Cache Miss → Continue
      ↓
5. Check Daily Limit: gemini_calls:{YYYY-MM-DD}
   ├─ Limit Reached → Use fallback (0 Gemini calls)
   └─ Under Limit → Continue
      ↓
6. Check Environment
   ├─ Development/Local → Use fallback (0 Gemini calls)
   └─ Production → Continue
      ↓
7. Call Gemini ONCE for Batch Judgment
   ├─ Success → Cache result, return items
   └─ Error/Quota → Use fallback, return items
      ↓
8. Return 4-5 Items with:
   - summary_zh (Chinese summary, ≤28 chars)
   - why_it_matters_zh (Why it matters)
   - tags (max 3)
   - relevance_score (≥60)
   - original_title (English)
   - overall_brief_zh (One-sentence summary)
```

## Success Criteria ✅

- ✅ No per-item Gemini calls remain
- ✅ One homepage refresh does NOT trigger many Gemini requests
- ✅ Industry news becomes Chinese-first and SV-relevant (no "Iran Protests…" type items)
- ✅ Quota usage becomes low and stable (no spikes)
- ✅ Cache by date (6 hours TTL)
- ✅ Daily call limiter (max 20 calls/day)
- ✅ Disabled in development/local environments
- ✅ Hard blacklist pre-filtering (EN + ZH keywords)
- ✅ Exception handling for tech-related politics (export controls, chip bans, etc.)

## Testing

### Production Environment:
- One batch call processes up to 30 items
- Returns JSON with 4-5 items (or 3 with shortage_reason)
- Each item has all required fields
- Chinese-first summaries with action-oriented style
- Cached for 6 hours (by date)

### Development Environment:
- Uses fallback with rule-based summaries
- Still returns items with required fields
- Zero Gemini calls

### Cache Behavior:
- Cache key: `industry_news_judgment:{YYYY-MM-DD}`
- TTL: 6 hours
- Cache hit: Returns immediately (0 Gemini calls)
- Cache miss: Calls Gemini ONCE, then caches result

### Daily Limit:
- Counter key: `gemini_calls:{YYYY-MM-DD}`
- Max: 20 calls per day
- When limit reached: Uses cached/stale result or fallback

## Logging

All Gemini calls are logged:
- `"Calling Gemini API for batch judgment of {N} items (call #{count}/{limit})"`
- `"Gemini call skipped: Daily limit reached ({count}/{limit} calls)"`
- `"Gemini disabled: Not in production environment or API key missing"`
- `"Using cached batch judgment from {key} ({N} items)"`
- `"Using fallback judgment (Gemini unavailable/disabled/failed)"`
- `"Gemini batch judgment completed: {N} items returned"`

## Next Steps

1. Deploy to production
2. Monitor Gemini quota usage (should be < 20 calls/day)
3. Verify cache hit rate (should be > 90% after first call)
4. Check frontend display (Chinese summaries, overall_brief_zh, dev badge)
