/**
 * Section 3: 吃喝玩乐
 * (1) Best Chinese restaurants within 10 miles (Google Places + Yelp) — 2x2 grid
 * (2) Best boba within 5 miles (Google Places + Yelp) — 2x2 grid
 * (3) Latest Chinese TV drama recommendations from YouTube — carousel
 * (4) North America gossip — horizontal carousel
 */
'use client'

import { PlaceGrid } from '../PlaceGrid'
import { EntertainmentGossipRow } from './EntertainmentGossipRow'

export function LifestyleSection() {
  return (
    <div className="space-y-3">
      {/* (1) & (2) Chinese Restaurants + Boba - Side by side on desktop, stacked on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* (1) Chinese Restaurants */}
        <PlaceGrid
          title="🍜 吃点好的"
          cuisineType="chinese"
          viewMoreHref="/food"
        />

        {/* (2) Boba */}
        <PlaceGrid
          title="🧋 肥宅快乐水"
          cuisineType="boba"
          viewMoreHref="/food"
        />
      </div>

      {/* (3) & (4) Entertainment & Gossip - Two-column layout */}
      <EntertainmentGossipRow />
    </div>
  )
}

