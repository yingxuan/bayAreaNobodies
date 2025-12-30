/**
 * YouTube Carousel Component - Right side of Row (col-span-5)
 * Reusable for both stock and tech videos
 */
'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { StandardCard } from './StandardCard'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type YouTubeVideo = {
  videoId: string
  title: string
  thumbnail: string
  duration?: string
  channelTitle?: string
  url?: string
}

type YouTubeCarouselProps = {
  category: 'stock' | 'tech'
  title: string
  viewMoreHref: string
  limit?: number
}

export function YouTubeCarousel({ category, title, viewMoreHref, limit }: YouTubeCarouselProps) {
  const [videos, setVideos] = useState<YouTubeVideo[]>([])
  const [loading, setLoading] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchVideos()
  }, [category, limit])

  const fetchVideos = async () => {
    setLoading(true)
    try {
      let endpoint = ''
      if (category === 'stock') {
        // Stock: each blogger's latest 1 video, minimum 6 videos total
        endpoint = `/youtube-channels/stock?limit_per_channel=1`
      } else {
        endpoint = `/youtube-channels/tech?limit_per_channel=3`
      }
      
      const res = await fetch(`${API_URL}${endpoint}`).catch(() => null)
      
      if (res?.ok) {
        const data = await res.json()
        let videoList = (data.items || []).map((item: any) => ({
          videoId: item.videoId,
          title: item.title,
          thumbnail: item.thumbnail,
          duration: item.duration || 'N/A',
          channelTitle: item.channelTitle,
          url: item.url || `https://www.youtube.com/watch?v=${item.videoId}`
        }))
        
        // For stock videos, show all available (no limit)
        // For other categories, apply limit if specified
        if (limit && category !== 'stock') {
          videoList = videoList.slice(0, limit)
        }
        
        setVideos(videoList)
      }
    } catch (error) {
      console.error(`Error fetching ${category} videos:`, error)
    } finally {
      setLoading(false)
    }
  }

  const handleVideoClick = (video: YouTubeVideo) => {
    const youtubeUrl = video.url || `https://www.youtube.com/watch?v=${video.videoId}`
    
    if (typeof window !== 'undefined') {
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
      if (isMobile) {
        const appUrl = `vnd.youtube:${video.videoId}`
        window.location.href = appUrl
        setTimeout(() => {
          window.open(youtubeUrl, '_blank')
        }, 500)
      } else {
        window.open(youtubeUrl, '_blank')
      }
    }
  }

  const fallbackThumbnail = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iIzFmMjkzNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'

  if (loading) {
    return (
      <StandardCard title={title}>
        <div className="flex items-center justify-center h-full">
          <div className="text-sm text-gray-500">加载中...</div>
        </div>
      </StandardCard>
    )
  }

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      // Calculate scroll amount: card width + gap
      // Mobile: 140px + 8px (gap-2) = 148px
      // Desktop: 160px + 12px (sm:gap-3) = 172px
      const isMobile = window.innerWidth < 640
      const cardWidth = isMobile ? 140 : 160
      const gap = isMobile ? 8 : 12
      const scrollAmount = cardWidth + gap
      
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      })
    }
  }

  // Don't render if no videos (empty sections are worse than missing sections)
  if (videos.length === 0) {
    return null
  }

  return (
    <div className="relative w-full max-w-full">
      {/* Left scroll button - Desktop only */}
      <button
        onClick={() => scroll('left')}
        className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-white rounded-full shadow-md p-2 hover:bg-gray-100 transition-colors hidden sm:flex items-center justify-center"
        aria-label="Scroll left"
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
      >
        <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      <StandardCard title={title} viewMoreHref={viewMoreHref} className="w-full max-w-full">
        {/* Carousel - Fixed height, horizontal scroll */}
        {/* CRITICAL FIX: ref must be on the element with overflow-x-auto */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-x-auto overflow-y-hidden pb-2 scrollbar-hide snap-x snap-mandatory"
        >
          <div className="flex gap-2 sm:gap-3 items-stretch h-[140px] sm:h-[160px]">
            {videos.map((video) => (
              <div
                key={video.videoId}
                onClick={() => handleVideoClick(video)}
                className="flex-shrink-0 min-w-[140px] sm:min-w-[160px] w-36 sm:w-40 h-[140px] sm:h-[160px] bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer flex flex-col snap-start"
              >
                {/* Thumbnail - Fixed height, aligned */}
                <div className="relative w-full h-20 bg-gray-100 flex-shrink-0">
                  {video.thumbnail ? (
                    <img
                      src={video.thumbnail}
                      alt={video.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.currentTarget.src = fallbackThumbnail
                      }}
                    />
                  ) : (
                    <img
                      src={fallbackThumbnail}
                      alt={video.title}
                      className="w-full h-full object-cover"
                    />
                  )}
                  {/* Duration badge */}
                  {video.duration && video.duration !== 'N/A' && (
                    <div className="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                      {video.duration}
                    </div>
                  )}
                </div>
                
                {/* Content - Fixed height, aligned */}
                <div className="p-1.5 flex-1 flex flex-col min-h-[60px]">
                  <h4 className="text-xs font-semibold text-gray-900 line-clamp-2 mb-0.5">
                    {video.title}
                  </h4>
                  {video.channelTitle && (
                    <div className="text-xs text-gray-500 line-clamp-1 mt-auto">
                      {video.channelTitle}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </StandardCard>
    </div>
  )
}

