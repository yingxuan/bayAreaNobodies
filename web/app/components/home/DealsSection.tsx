/**
 * Section 4: 遍地羊毛
 * Unified Deal Shelf - high-quality deals for Silicon Valley tech workers
 */
'use client'

import Link from 'next/link'
import { DealShelf } from '../DealShelf'

export function DealsSection() {
  return (
    <div className="space-y-3">
      {/* Section Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg sm:text-xl font-bold text-gray-900 truncate">遍地羊毛</h2>
        <Link href="/deals" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap flex-shrink-0">
          查看更多 →
        </Link>
      </div>

      {/* Unified Deal Shelf */}
      <DealShelf />
    </div>
  )
}

