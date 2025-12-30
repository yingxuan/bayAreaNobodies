/**
 * Shared Carousel Component - Fixes scroll button issues
 * 
 * Root cause of scroll bug:
 * - The ref was attached to the inner flex container
 * - But overflow-x-auto was on the parent wrapper
 * - Buttons tried to scroll the wrong element
 * 
 * Fix:
 * - Attach ref to the element with overflow-x-auto
 * - Calculate scroll amount = card width + gap
 * - Ensure buttons are siblings of scroll container
 */
'use client'

import { useRef, ReactNode } from 'react'
import React from 'react'

type SharedCarouselProps = {
  children: ReactNode
  cardWidth?: number // min-w-[240px] = 240px, sm:min-w-[260px] = 260px
  gap?: number // gap-3 = 12px, sm:gap-4 = 16px
  maxVisible?: number // Limit visible items for UX
  className?: string
}

export function SharedCarousel({ 
  children, 
  cardWidth = 240, // Default mobile width
  gap = 12, // Default gap
  maxVisible = 6, // Limit to 6 items max
  className = '' 
}: SharedCarouselProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  
  // Handle children: convert to array and limit
  const childrenArray = React.Children.toArray(children)
  const limitedChildren = childrenArray.slice(0, maxVisible)

  const scroll = (direction: 'left' | 'right') => {
    if (!scrollRef.current) return
    
    // Calculate scroll amount: card width + gap
    // On mobile: 240px + 12px = 252px
    // On desktop (sm): 260px + 16px = 276px
    const isMobile = window.innerWidth < 640
    const scrollCardWidth = isMobile ? cardWidth : cardWidth + 20 // sm:min-w-[260px]
    const scrollGap = isMobile ? gap : gap + 4 // sm:gap-4
    const scrollAmount = scrollCardWidth + scrollGap
    
    scrollRef.current.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth'
    })
  }

  return (
    <div className={`relative ${className}`}>
      {/* Left scroll button - Desktop only */}
      <button
        onClick={() => scroll('left')}
        className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-white rounded-full shadow-md p-2 hover:bg-gray-100 transition-colors hidden sm:flex items-center justify-center"
        aria-label="Scroll left"
        type="button"
      >
        <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {/* Right scroll button - Desktop only */}
      <button
        onClick={() => scroll('right')}
        className="absolute right-0 top-1/2 -translate-y-1/2 z-20 bg-white rounded-full shadow-md p-2 hover:bg-gray-100 transition-colors hidden sm:flex items-center justify-center"
        aria-label="Scroll right"
        type="button"
      >
        <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Scroll container - ref attached to element with overflow-x-auto */}
      <div
        ref={scrollRef}
        className="overflow-x-auto scrollbar-hide snap-x snap-mandatory pb-2"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
      >
        <div className="flex gap-3 sm:gap-4">
          {limitedChildren}
        </div>
      </div>
    </div>
  )
}

