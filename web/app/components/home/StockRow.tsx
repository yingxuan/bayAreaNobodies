/**
 * Stock Row - 7/5 layout
 * Left: StockSummaryCard (col-span-7)
 * Right: YouTubeCarousel for stock analysis videos (col-span-5)
 */
'use client'

import { StockSummaryCard } from './StockSummaryCard'
import { YouTubeCarousel } from './YouTubeCarousel'

export function StockRow() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      {/* Left: Stock Summary (7 columns) */}
      <div className="lg:col-span-7 flex">
        <StockSummaryCard />
      </div>

      {/* Right: Stock Analysis Videos (5 columns) */}
      <div className="lg:col-span-5 flex">
        <YouTubeCarousel
          category="stock"
          title="📺 美股分析视频"
          viewMoreHref="/videos/stocks"
          limit={5}
        />
      </div>
    </div>
  )
}

