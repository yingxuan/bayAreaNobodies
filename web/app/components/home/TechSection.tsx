/**
 * Section 2: 行业新闻
 * (1) AI industry realtime news (text list) - Left 7 columns
 * (2) Latest tech news videos on YouTube - Right 5 columns
 */
'use client'

import { TechNewsList } from './TechNewsList'
import { TechVideoCards } from './TechVideoCards'

export function TechSection() {
  return (
    <div className="space-y-3 sm:space-y-4">
      {/* Section Header - Increased visual weight */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 truncate">行业新闻</h2>
      </div>

      {/* News & Videos Row - 12-column grid: 7/5 split on desktop, stacked on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 sm:gap-4 items-start">
        {/* Left: AI 行业要闻 - 7 columns on desktop */}
        <div className="lg:col-span-7 bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-4 flex flex-col">
          <TechNewsList />
        </div>

        {/* Right: 科技新闻视频 - 5 columns on desktop */}
        <div className="lg:col-span-5 bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-4 flex flex-col">
          <TechVideoCards />
        </div>
      </div>
    </div>
  )
}

