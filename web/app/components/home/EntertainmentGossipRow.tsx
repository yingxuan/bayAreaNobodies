/**
 * Entertainment & Gossip Row - Two-column layout
 * Left: 追剧 (Entertainment vertical list, max 3)
 * Right: 吃瓜 (Gossip text list)
 */
'use client'

import Link from 'next/link'
import { EntertainmentList } from './EntertainmentList'
import { GossipTextList } from './GossipTextList'

export function EntertainmentGossipRow() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
      {/* Left: 追剧 - 7 columns on desktop */}
      <div className="lg:col-span-7 bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-4 flex flex-col h-full">
        {/* Header - Fixed height for alignment */}
        <div className="flex items-center justify-between mb-2 flex-shrink-0 min-h-[52px]">
          <h3 className="text-base font-bold text-gray-900">🎬 追剧</h3>
          <Link href="/videos/entertainment" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap">
            更多 →
          </Link>
        </div>
        
        {/* Vertical list - max 3 items */}
        <div className="flex-1">
          <EntertainmentList />
        </div>
      </div>

      {/* Right: 吃瓜 - 5 columns on desktop */}
      <div className="lg:col-span-5 bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-4 flex flex-col h-full">
        {/* Header - Fixed height for alignment */}
        <div className="flex items-center justify-between mb-2 flex-shrink-0 min-h-[52px]">
          <h3 className="text-base font-bold text-gray-900">🍉 吃瓜</h3>
          <Link href="/gossip" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap">
            更多 →
          </Link>
        </div>
        
        {/* Text List */}
        <div className="flex-1">
          <GossipTextList />
        </div>
      </div>
    </div>
  )
}

