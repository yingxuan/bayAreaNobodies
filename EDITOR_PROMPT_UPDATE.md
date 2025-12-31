# Editor Prompt Update - 湾区码农今日简报

## Changes Made

### 1. Updated Gemini Prompt ✅
Changed from simple summarization to "总编辑" (Editor-in-Chief) role:

**New Role**: "湾区码农今日简报"的总编辑
- Goal: Not comprehensive reporting, but judgment for Bay Area tech workers
- Focus: What's most worth watching today (tech/AI/big tech/stocks/jobs)

### 2. Hard Constraints ✅
- **Only care about**: AI, chips/semiconductors, cloud, Big Tech (NVDA/MSFT/META/GOOG/AMZN/AAPL/TSLA), earnings/guidance, layoffs/hiring, regulation impact on tech stocks, major product/model releases, M&A
- **Filter out**: World politics/war/protests/social news (unless directly affecting tech stocks or big tech business, e.g., export controls/chip bans/antitrust rulings)

### 3. JSON Schema Output ✅
**Required fields per item**:
- `summary_zh`: 1 sentence (≤28 chars)
- `why_it_matters_zh`: 1 sentence (impact on money/job/tech)
- `tags`: ≤3 tags from: AI, LLM, NVDA, MSFT, META, GOOG, AAPL, AMZN, TSLA, Chips, Cloud, Security, Earnings, Layoffs, Regulation, Startups
- `relevance_score`: 0-100 (only ≥60 returned)
- `reason`: Short explanation why selected
- `source_name`: Source name
- `url`: Original article URL
- `original_title`: Original English title (optional)

**Response format**:
```json
{
  "items": [...],
  "shortage_reason": null  // or explanation if <4 items
}
```

### 4. Chinese Expression Style ✅
- Like "朋友提醒你今天该盯啥" (friend reminding you what to watch today)
- Short, direct, action-oriented
- Focus on impact on money/work

### 5. Output Requirements ✅
- Must return 4-5 items
- If insufficient candidates, return 3 items with `shortage_reason`
- No English titles as main content (only in `original_title` field)

## Implementation

### Updated Files

1. **`api/app/services/news_judgment_service.py`**
   - Updated `judge_news_batch_with_gemini()` prompt
   - Changed from pipe-delimited text to JSON parsing
   - Added URL matching logic
   - Added all required fields mapping

2. **`api/app/services/industry_news_service.py`**
   - Updated `format_industry_news_item()` to include `reason` field
   - Uses `source_name` from Gemini if available

### JSON Parsing Logic

- Extracts JSON from response (handles markdown code blocks)
- Maps Gemini items back to original items by URL or title
- Preserves all original fields
- Adds Gemini judgment fields

## Testing

When Gemini is enabled (production):
- One batch call processes up to 20 items
- Returns JSON with 4-5 items (or 3 with shortage_reason)
- Each item has all required fields
- Chinese-first summaries with action-oriented style

When Gemini is disabled (development):
- Uses fallback with rule-based summaries
- Still returns items with required fields

## Success Criteria ✅

- ✅ Prompt reflects "总编辑" role
- ✅ Hard constraints clearly defined
- ✅ JSON schema enforced
- ✅ All required fields included
- ✅ Chinese expression style: friend-reminder style
- ✅ 4-5 items returned (or 3 with shortage_reason)
- ✅ No English titles as main content
