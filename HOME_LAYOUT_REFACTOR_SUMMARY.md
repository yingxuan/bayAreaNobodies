# Homepage Layout Refactor - Summary

## Design Goals
Reduce visual clutter and improve information hierarchy without changing data sources or features.

## Key Changes

### 1. Financial Summary Bar (Highest Priority)
- **Converted** from card to full-width horizontal bar
- **Component**: `FinancialSummaryBar.tsx`
- **Layout**: `col-span-12` (full width)
- **Content**: Total assets, today's gain/loss, top movers, action link
- **Purpose**: Answers "What should a Bay Area tech worker care about today?" - financial status

### 2. News & Videos (Secondary Priority)
- **Layout**: 6/6 grid (2 columns, equal height)
- **Left**: Tech Catalyst News Card (text-only, no thumbnails)
- **Right**: Tech Videos Carousel (max 3 thumbnails)
- **Components**: `TechCatalystNewsCard`, `YouTubeCarousel`
- **Styling**: Consistent with `StandardCard` wrapper

### 3. Stock Analysis (Secondary Priority)
- **Layout**: 6/6 grid (2 columns, equal height)
- **Left**: Market Analysis placeholder (text-only)
- **Right**: Stock Videos Carousel (max 3 thumbnails)
- **Components**: `YouTubeCarousel`

### 4. Lifestyle Content (Tertiary Priority)
- **Layout**: Collapsible sections (collapsed by default)
- **Sections**:
  - 🍜 吃点好的 (Chinese restaurants)
  - 🧋 肥宅快乐水 (Boba)
  - 💰 遍地羊毛 (Deals)
  - 🎬 今晚追什么 (Entertainment)
  - 🗣 北美八卦 (Gossip)
- **Component**: `CollapsibleSection.tsx`
- **Purpose**: Reduces visual clutter, allows users to expand when needed

## Layout Structure

```
┌─────────────────────────────────────────┐
│ CompactTopBar (Market Indicators)       │
├─────────────────────────────────────────┤
│ TodayAlertBar (Must-do Actions)         │
├─────────────────────────────────────────┤
│ FinancialSummaryBar (Full Width)        │ ← Highest Priority
├──────────────────┬──────────────────────┤
│ Tech News        │ Tech Videos          │ ← Secondary (6/6)
│ (Text-only)     │ (Max 3 thumbnails)   │
├──────────────────┼──────────────────────┤
│ Market Analysis  │ Stock Videos         │ ← Secondary (6/6)
│ (Text-only)     │ (Max 3 thumbnails)   │
├─────────────────────────────────────────┤
│ 🍜 吃点好的 (Collapsed)                  │ ← Tertiary
├─────────────────────────────────────────┤
│ 🧋 肥宅快乐水 (Collapsed)                 │ ← Tertiary
├─────────────────────────────────────────┤
│ 💰 遍地羊毛 (Collapsed)                   │ ← Tertiary
├─────────────────────────────────────────┤
│ 🎬 今晚追什么 (Collapsed)                 │ ← Tertiary
├─────────────────────────────────────────┤
│ 🗣 北美八卦 (Collapsed)                    │ ← Tertiary
└─────────────────────────────────────────┘
```

## Grid System

- **Strict 12-column grid**: `grid grid-cols-12`
- **At most 2 columns per row**: `lg:col-span-6` for side-by-side
- **Equal height cards**: `flex` wrapper with `h-full` on cards
- **Consistent spacing**: `gap-4` between grid items

## Component Updates

### New Components
1. `FinancialSummaryBar.tsx` - Full-width financial summary
2. `CollapsibleSection.tsx` - Collapsible wrapper for low-priority content
3. `StandardCard.tsx` - Consistent card styling (padding, header, footer)

### Modified Components
1. `TechCatalystNewsCard.tsx` - Uses `StandardCard`, text-only (no thumbnails)
2. `YouTubeCarousel.tsx` - Uses `StandardCard`, limit reduced to 3 videos
3. `EntertainmentCarousel.tsx` - Added `hideTitle` prop for use in CollapsibleSection
4. `GossipCarousel.tsx` - Added `hideTitle` prop for use in CollapsibleSection
5. `CarouselSection.tsx` - Made title optional (empty string hides header)

## Design Constraints Met

✅ **12-column grid system**: All sections use `grid-cols-12`  
✅ **At most 2 columns per row**: 6/6 layout for news/videos  
✅ **Equal height cards**: `flex` wrapper ensures height consistency  
✅ **Clear semantic purpose**: Each section has distinct purpose  
✅ **Financial summary highest priority**: Full-width bar at top  
✅ **News/videos secondary**: 6/6 layout, text-only news  
✅ **Lifestyle tertiary**: Collapsed by default, doesn't compete visually  
✅ **Max 3 video thumbnails**: Reduced from 5 to 3  
✅ **Text-only news**: No thumbnails in news sections  
✅ **Horizontal carousels**: Food, drinks, deals remain as carousels  
✅ **Consistent styling**: `StandardCard` ensures uniform appearance  

## Information Hierarchy

1. **Above-the-fold**: Financial summary bar (full width)
2. **Secondary**: News and videos (6/6 layout, equal height)
3. **Tertiary**: Lifestyle content (collapsed, expandable)

## Scannability Improvements

1. **Reduced visual clutter**: Collapsed sections hide low-priority content
2. **Clear hierarchy**: Financial → News/Videos → Lifestyle
3. **Consistent styling**: All cards use same padding, header, footer
4. **Text-first news**: No thumbnails compete with text content
5. **Limited videos**: Max 3 per section reduces cognitive load
6. **Equal heights**: Cards in same row have same height, reducing visual noise

## CSS Classes Used

- **Grid**: `grid grid-cols-12 gap-4`
- **Columns**: `col-span-12` (full), `col-span-6` (half)
- **Equal height**: `flex` wrapper, `h-full` on cards
- **Cards**: `bg-white rounded-xl shadow-sm border border-gray-200 p-4`
- **Headers**: `min-h-[44px] flex items-center justify-between`
- **Footers**: `text-xs text-blue-600 hover:text-blue-700`

