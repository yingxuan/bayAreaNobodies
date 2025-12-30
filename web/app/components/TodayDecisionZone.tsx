/**
 * Today Decision Zone - High-density decision area
 * Combines: Stock Assets (left) + Today Reminder (right) + News (bottom bar)
 * Goal: Compress 3 modules into one cohesive block
 */
'use client'

import { StockAssetsCard } from './StockAssetsCard'
import { TodayMustDo } from './TodayMustDo'
import { NewsDigestCard } from './NewsDigestCard'

export function TodayDecisionZone() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Top: Stock Assets (left) + Today Reminder (right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 border-b border-gray-100">
        <div className="border-r-0 lg:border-r border-gray-100">
          <StockAssetsCard />
        </div>
        <div>
          <TodayMustDo />
        </div>
      </div>

      {/* Bottom: News horizontal bar */}
      <div className="border-t border-gray-100">
        <NewsDigestCard />
      </div>
    </div>
  )
}

