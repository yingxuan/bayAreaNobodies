/**
 * Tech Row - 7/5 layout
 * Left: TechCatalystNewsCard (col-span-7)
 * Right: YouTubeCarousel for tech news videos (col-span-5)
 */
'use client'

import { TechCatalystNewsCard } from './TechCatalystNewsCard'
import { YouTubeCarousel } from './YouTubeCarousel'

export function TechRow() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      {/* Left: Tech Catalyst News (7 columns) */}
      <div className="lg:col-span-7 flex">
        <TechCatalystNewsCard />
      </div>

      {/* Right: Tech News Videos (5 columns) */}
      <div className="lg:col-span-5 flex">
        <YouTubeCarousel
          category="tech"
          title="📺 科技新闻解读"
          viewMoreHref="/videos/tech"
          limit={5}
        />
      </div>
    </div>
  )
}

