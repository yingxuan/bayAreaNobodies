/**
 * Section 4: 遍地羊毛
 * ONE section only (no duplicates), with tabs inside (Fast food / Grocery / Apps)
 */
'use client'

import { DealsCarousel } from '../DealsCarousel'

export function DealsSection() {
  return (
    <div className="space-y-3">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg sm:text-xl font-bold text-gray-900 truncate">遍地羊毛</h2>
      </div>

      {/* Deals with Tabs */}
      <DealsCarousel />
    </div>
  )
}

