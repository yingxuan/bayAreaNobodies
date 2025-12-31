# Gemini Quota Explosion Fix

## Problem
Gemini API was being called for EVERY news item individually, causing quota explosion.

## Solution Implemented

### 1. Batch Processing ✅
**Before**: One Gemini call per news item (could be 20+ calls per page load)
**After**: ONE Gemini call per request for entire batch

- Function: `judge_news_batch_with_gemini(items: List[Dict])`
- Processes up to 20 items in a single call
- Returns top 5 items with summary_zh, why_it_matters_zh, relevance_score

### 2. Environment-Based Disabling ✅
**Development/Local**: Gemini completely disabled
**Production**: Gemini enabled only if:
- `ENVIRONMENT=production` or `ENVIRONMENT=prod`
- `GEMINI_API_KEY` is set
- `GEMINI_AVAILABLE=True`

```python
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in ["production", "prod"]
GEMINI_ENABLED = GEMINI_AVAILABLE and GEMINI_API_KEY and IS_PRODUCTION
```

### 3. Date-Based Cache Key ✅
**Before**: `news_judgment:{url_hash}` (per-URL, TTL=1 hour)
**After**: `industry_news_judgment:YYYY-MM-DD` (per-day, TTL=6 hours)

- Cache key: `industry_news_judgment:2025-12-30`
- TTL: 21600 seconds (6 hours)
- All requests on the same day use the same cache

### 4. Daily Call Limiter ✅
- Max calls per day: 10 (configurable via `GEMINI_DAILY_LIMIT`)
- Counter key: `gemini_daily_calls:YYYY-MM-DD`
- If limit reached: Silently skip Gemini, use cached result or fallback
- Counter resets daily (24-hour expiry)

### 5. Explicit Logging ✅
All Gemini operations are logged:
- `"Calling Gemini API for batch judgment of N items"` - When calling
- `"Gemini disabled: Not in production environment"` - When disabled
- `"Gemini call skipped: Daily limit reached"` - When skipped due to limit
- `"Using fallback judgment (Gemini unavailable/disabled/failed)"` - When using fallback
- `"Using cached batch judgment from {key}"` - When using cache

## Impact

### Before
- **Per page load**: 20+ Gemini calls (one per item)
- **Per day**: Potentially hundreds of calls
- **Quota**: Exhausted quickly

### After
- **Per page load**: 0-1 Gemini calls (usually 0 due to cache)
- **Per day**: Maximum 10 calls (hard limit)
- **Local dev**: 0 calls (Gemini disabled)
- **Quota**: Protected by daily limit + caching

## Files Modified

1. **`api/app/services/news_judgment_service.py`** (COMPLETELY REWRITTEN)
   - Removed per-item `judge_news_item_with_gemini()`
   - Added batch `judge_news_batch_with_gemini()`
   - Added `get_or_judge_news_batch()` with caching
   - Added environment check
   - Added daily call limiter
   - Added explicit logging

2. **`api/app/services/industry_news_service.py`** (MODIFIED)
   - Changed from per-item loop to batch call
   - Now calls `get_or_judge_news_batch(candidates)` once

## Testing

### Local Development
```bash
# Environment: development
# Result: Gemini disabled, uses fallback
# Calls: 0
```

### Production
```bash
# Environment: production
# Result: Gemini enabled, uses batch call
# Calls: 1 per day (after first call, uses cache)
```

### Cache Verification
```bash
# Check cache key
redis-cli KEYS "industry_news_judgment:*"
# Should see: industry_news_judgment:2025-12-30

# Check daily counter
redis-cli KEYS "gemini_daily_calls:*"
# Should see: gemini_daily_calls:2025-12-30
```

## Configuration

Environment variables:
- `ENVIRONMENT`: Set to "production" to enable Gemini (default: "development")
- `GEMINI_API_KEY`: Required for Gemini calls
- `GEMINI_DAILY_LIMIT`: Max calls per day (default: 10)

## Success Criteria ✅

- ✅ One page load triggers at most ONE Gemini call (usually zero)
- ✅ Local dev triggers ZERO Gemini calls
- ✅ Daily limit prevents quota explosion
- ✅ Date-based cache ensures same-day requests use cache
- ✅ Explicit logging for all Gemini operations
