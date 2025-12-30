/**
 * Section 1: 早日财富自由
 * (1) My portfolio holdings change (P&L summary)
 * (2) Index row: SPY, Gold, BTC, California Jumbo Loan Rate, Powerball Jackpot
 * (3) Latest videos from US stock/finance YouTubers
 */
'use client'

import { WealthSummaryHeader } from './WealthSummaryHeader'
import { YouTubeCarousel } from './YouTubeCarousel'

export function WealthSection() {
  return (
    <div className="space-y-3">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg sm:text-xl font-bold text-gray-900 truncate">早日财富自由</h2>
      </div>

      {/* (1) Portfolio Summary + Index Row */}
      <WealthSummaryHeader />

      {/* (2) Stock Videos */}
      <div className="w-full">
        <YouTubeCarousel
          category="stock"
          title="📺 美股分析视频"
          viewMoreHref="/videos/stocks"
        />
      </div>
    </div>
  )
}

