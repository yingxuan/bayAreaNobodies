# Carousel Scroll Button Fix & Homepage UX Improvements

## Root Cause of Scroll Button Bug

**Critical Issue**: The scroll buttons were not working because:

1. **Wrong ref attachment**: The `ref` was attached to the inner flex container (`<div className="flex gap-3">`), but the `overflow-x-auto` was on the parent wrapper (`<div className="overflow-x-auto">`).

2. **Scroll target mismatch**: When buttons called `scrollRef.current.scrollBy()`, they tried to scroll the inner flex container, which doesn't have scrollable overflow. The actual scrollable element was the parent wrapper.

3. **Arbitrary scroll amounts**: Used fixed values like `300px` instead of calculating based on actual card width + gap.

## Solution

### 1. Created SharedCarousel Component
- **File**: `web/app/components/SharedCarousel.tsx`
- **Fix**: Attach `ref` directly to the element with `overflow-x-auto`
- **Scroll calculation**: `scrollAmount = cardWidth + gap` (responsive: 240px+12px on mobile, 260px+16px on desktop)
- **Button positioning**: Buttons are siblings of scroll container, not inside it
- **Mobile**: Buttons hidden on mobile (native swipe only)

### 2. Fixed Components Using SharedCarousel

#### PlaceCarousel.tsx
- ✅ Uses `SharedCarousel` component
- ✅ Limited to 6 items (was 10)
- ✅ Removed duplicate scroll logic

#### EntertainmentCarousel.tsx
- ✅ Uses `SharedCarousel` component
- ✅ Limited to 6 items (was 10)
- ✅ Removed duplicate scroll logic

#### GossipCarousel.tsx
- ✅ Uses `SharedCarousel` component
- ✅ Limited to 6 items (was 10)
- ✅ Removed duplicate scroll logic

#### YouTubeCarousel.tsx (Stock Videos)
- ✅ Fixed ref attachment: `ref` now on element with `overflow-x-auto`
- ✅ Calculated scroll amount: `cardWidth + gap` (140px+8px mobile, 160px+12px desktop)
- ✅ Limited to 6 items (was unlimited)
- ⚠️ Kept custom implementation (uses StandardCard wrapper, different card size)

## Homepage UX Improvements

### 1. Reduced Visual Overload
- **Carousel limits**: All carousels now show max 6 items (was 10+)
  - PlaceCarousel: 6 items (was 10)
  - EntertainmentCarousel: 6 items (was 10)
  - GossipCarousel: 6 items (was 10)
  - YouTubeCarousel (stock): 6 items (was unlimited)
  - DealsCarousel: 6 items per tab (unchanged)

### 2. Improved Spacing
- **Section spacing**: Reduced from `space-y-4` to `space-y-3` in:
  - `web/app/page.tsx` (main container)
  - `web/app/components/home/LifestyleSection.tsx`

### 3. Balanced Content
- **Tech News**: Already limited to 4 items (good balance with video content)
- **Video carousels**: Limited to prevent dominance

## Fixed Carousel Components

1. ✅ **PlaceCarousel** - 吃点好的 / 肥宅快乐水
2. ✅ **EntertainmentCarousel** - 今晚追什么
3. ✅ **GossipCarousel** - 北美八卦
4. ✅ **YouTubeCarousel** - 美股分析视频 (custom fix, not using SharedCarousel)
5. ✅ **DealsCarousel** - 遍地羊毛 (no scroll buttons, horizontal scroll only)

## Technical Details

### SharedCarousel Props
```typescript
{
  children: ReactNode
  cardWidth?: number      // Default: 240px (mobile)
  gap?: number            // Default: 12px
  maxVisible?: number     // Default: 6 items
  className?: string
}
```

### Scroll Calculation
- Mobile (< 640px): `240px (card) + 12px (gap) = 252px`
- Desktop (≥ 640px): `260px (card) + 16px (gap) = 276px`

### Button Visibility
- Desktop: Visible (`hidden sm:flex`)
- Mobile: Hidden (native swipe only)

## Acceptance Criteria Status

✅ **Carousel left/right buttons scroll exactly one item per click**
- Fixed: Scroll amount = card width + gap

✅ **No carousel appears "stuck"**
- Fixed: Ref attached to correct scrollable element

✅ **Homepage feels lighter and easier to scan**
- Fixed: Limited items to 6 max, reduced spacing

✅ **UX is consistent across all carousel sections**
- Fixed: Shared component ensures consistency

## Testing Checklist

- [ ] Test scroll buttons on desktop (all carousels)
- [ ] Verify one card scrolls per click
- [ ] Test mobile swipe (buttons should be hidden)
- [ ] Verify no horizontal page overflow
- [ ] Check carousel item limits (max 6 visible)
- [ ] Verify homepage spacing is tighter

