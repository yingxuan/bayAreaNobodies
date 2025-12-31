# Judgment Layer Implementation Summary

## Overview
Added a "judgment layer" to transform the homepage from content aggregation to a decision dashboard. Each section now answers ONE daily question with opinionated, filtered judgments generated using Gemini API.

## Core Principle
**Homepage = decision dashboard, not content feed**

Every section:
- Answers ONE daily question
- Shows very limited items
- Includes ONE short judgment sentence (generated)
- Prefers Chinese output
- Is cached and fast

## Implementation

### 1. Shared Judgment Service (`api/app/services/judgment_service.py`)

Centralized service for generating opinionated judgments using Gemini API.

**Key Features:**
- All judgments cached (TTL varies by section)
- Failure-safe (returns None on error, never blocks rendering)
- Chinese-first output
- Character limits enforced

**Functions:**
- `generate_portfolio_judgment()` - Portfolio status judgment
- `generate_mortgage_judgment()` - Mortgage/refi timing judgment
- `generate_offer_market_judgment()` - Market temperature + risk note
- `generate_food_place_tag()` - Optional short tags for places
- `generate_entertainment_description()` - Optional descriptions

### 2. API Endpoints (`/api/judgment/*`)

**`/judgment/portfolio`**
- Question: "我今天的钱整体状态如何？"
- Input: day_gain, day_gain_percent, top_movers, index_change
- Output: Judgment sentence (≤25 Chinese chars)
- Cache: 30 minutes
- Example: "今天是结构性波动，主要由 NVDA 拖累，非系统性下跌"

**`/judgment/mortgage`**
- Question: "我现在该不该关心买房或 refi？"
- Input: rate_30y, rate_7_1_arm, rate_trend (optional)
- Output: Judgment sentence (≤25 Chinese chars)
- Cache: 1 hour
- Example: "利率连续横盘，短期 refi 价值不高"

**`/judgment/offer-market`**
- Question: "市场现在给码农什么价？"
- Input: Analyzes recent offers, layoff/hiring news
- Output: `{temperature: "冷"|"正常"|"热", risk_note: "≤25 chars"}`
- Cache: 1 hour

**`/judgment/food-tag`** (Optional)
- Generates short tags for food/boba places
- Output: ≤4 Chinese chars (e.g., "稳", "排队多", "适合带娃")
- Cache: 24 hours

**`/judgment/entertainment-description`** (Optional)
- Generates 1-line descriptions for entertainment content
- Output: ≤30 Chinese chars
- Cache: 6 hours

### 3. Frontend Integration

#### Portfolio Section (`FinancialSummaryBar.tsx`)
- Fetches judgment after portfolio data loads
- Displays judgment below KPIs in italic gray text
- Non-blocking: renders numbers even if judgment fails

#### Mortgage Section (`IndexRow.tsx`)
- Fetches judgment when mortgage rates are available
- Displays judgment below rate indicators
- Non-blocking: shows rates even if judgment fails

#### Industry News Section
- Already has Gemini integration from previous refactor
- Uses `/news/industry` endpoint with Chinese summaries
- Judgment embedded in `why_it_matters_zh` field

## Gemini Usage Rationale

### ✅ Use Gemini For:
1. **Portfolio Judgment**: Requires understanding of market structure, top movers, and index correlation
2. **Mortgage Judgment**: Requires trend analysis and timing advice
3. **Offer Market Temperature**: Requires analyzing multiple signals (offers, layoffs, hiring) to infer market state
4. **Industry News Summarization**: Already implemented - requires relevance ranking and Chinese summarization
5. **Food Tags** (Optional): Requires understanding place characteristics
6. **Entertainment Descriptions** (Optional): Requires content understanding

### ❌ Do NOT Use Gemini For:
- Simple math (portfolio calculations)
- Formatting (number formatting, date formatting)
- Static rendering (UI components)
- Distance calculations
- Rating sorting
- Data fetching

## Caching Strategy

| Section | Cache TTL | Rationale |
|---------|-----------|-----------|
| Portfolio | 30 min | Changes frequently with market |
| Mortgage | 1 hour | Rates change slowly |
| Offer Market | 1 hour | Market sentiment changes slowly |
| Food Tags | 24 hours | Places don't change often |
| Entertainment | 6 hours | Content updates periodically |

**Cache Keys:**
- Based on data hash (content-based)
- Prevents re-generating for identical inputs
- Automatic invalidation on data change

## Failure Handling

**All judgments are failure-safe:**
1. If Gemini API unavailable → Returns None
2. If API call fails → Returns None
3. If cache miss and generation fails → Returns None
4. Frontend always renders numbers/data even without judgment
5. No loading spinners for judgments (async, non-blocking)

## Performance

- **Non-blocking**: Judgments fetched asynchronously after data loads
- **Cached**: Reduces API calls significantly
- **Parallel**: Multiple judgments can be fetched simultaneously
- **Timeout**: Gemini calls have implicit timeout (handled by library)

## Files Created/Modified

### New Files:
- `api/app/services/judgment_service.py` - Core judgment service
- `api/app/routers/judgment.py` - API endpoints
- `JUDGMENT_LAYER_IMPLEMENTATION.md` - This document

### Modified Files:
- `api/main.py` - Added judgment router
- `web/app/components/home/FinancialSummaryBar.tsx` - Added portfolio judgment
- `web/app/components/home/IndexRow.tsx` - Added mortgage judgment

## Next Steps (Optional Enhancements)

1. **Offer Market Section**: Create UI component to display temperature + risk note
2. **Food/Boba Tags**: Add tag display to PlaceCard components
3. **Entertainment Descriptions**: Add to video/entertainment cards
4. **Gossip Deduplication**: Use Gemini to deduplicate similar gossip titles

## Testing

Test endpoints:
```bash
# Portfolio judgment
curl "http://localhost:8000/judgment/portfolio?day_gain=1000&day_gain_percent=2.5&top_movers=[{\"ticker\":\"NVDA\",\"day_gain_percent\":3.2}]"

# Mortgage judgment
curl "http://localhost:8000/judgment/mortgage?rate_30y=6.5&rate_7_1_arm=6.2"

# Offer market judgment
curl "http://localhost:8000/judgment/offer-market"
```

## Success Criteria Met

✅ Each section answers ONE daily question  
✅ Shows very limited items  
✅ Includes ONE short judgment sentence (generated)  
✅ Prefers Chinese output  
✅ Cached and fast  
✅ Non-blocking (never blocks page render)  
✅ Failure-safe (graceful degradation)  
✅ Uses Gemini only for natural language understanding, not simple operations  

## Notes

- All Gemini calls are server-side only
- Judgments are opinionated and filtered (not raw data)
- Character limits ensure scannable homepage (3-5 minutes to scan)
- User feels "this site already thought for me"
