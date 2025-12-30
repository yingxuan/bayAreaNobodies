/**
 * Entertainment Carousel - 🎬 今晚追什么
 * YouTube latest TV shows / Variety shows
 * Target: Increase engagement and next-day open rate
 */
'use client'

import { useState, useEffect } from 'react'
import { SharedCarousel } from './SharedCarousel'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type YouTubeVideo = {
  videoId: string
  title: string
  title_cn?: string
  thumbnail: string
  channelTitle: string
  url?: string
  type?: 'tv' | 'variety'
}

type EntertainmentCardProps = {
  video: YouTubeVideo
}

function EntertainmentCard({ video }: EntertainmentCardProps) {
  const handleClick = () => {
    // Construct YouTube URL
    const youtubeUrl = video.url || `https://www.youtube.com/watch?v=${video.videoId}`
    
    // Mobile: try to open YouTube app, fallback to web
    if (typeof window !== 'undefined') {
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
      if (isMobile) {
        // Try YouTube app URL first
        const appUrl = `vnd.youtube:${video.videoId}`
        window.location.href = appUrl
        // Fallback to web after short delay
        setTimeout(() => {
          window.open(youtubeUrl, '_blank')
        }, 500)
      } else {
        window.open(youtubeUrl, '_blank')
      }
    }
  }

  const displayTitle = video.title_cn || video.title
  
  // Fallback thumbnail (SVG data URI)
  const fallbackThumbnail = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iIzFmMjkzNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 min-w-[240px] sm:min-w-[260px] bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start"
    >
      {/* Thumbnail */}
      <div className="relative w-full h-32 bg-gray-100">
        {video.thumbnail ? (
          <img
            src={video.thumbnail}
            alt={displayTitle}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.src = fallbackThumbnail
            }}
          />
        ) : (
          <img
            src={fallbackThumbnail}
            alt={displayTitle}
            className="w-full h-full object-cover"
          />
        )}
      </div>
      
      {/* Content */}
      <div className="p-3">
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-1.5">
          {displayTitle}
        </h4>
        <div className="text-xs text-gray-600 line-clamp-1">
          {video.channelTitle}
        </div>
      </div>
    </div>
  )
}

type EntertainmentCarouselProps = {
  hideTitle?: boolean
}

export function EntertainmentCarousel({ hideTitle = false }: EntertainmentCarouselProps = {}) {
  const [videos, setVideos] = useState<YouTubeVideo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    setLoading(true)
    try {
      // Fetch both TV and Variety shows
      const [tvRes, varietyRes] = await Promise.all([
        fetch(`${API_URL}/entertainment/youtube?type=tv&limit=8`).catch(() => null),
        fetch(`${API_URL}/entertainment/youtube?type=variety&limit=8`).catch(() => null)
      ])

      let allVideos: YouTubeVideo[] = []

      if (tvRes?.ok) {
        const tvData = await tvRes.json()
        const tvVideos = (tvData.items || []).map((item: any) => ({
          ...item,
          type: 'tv' as const
        }))
        allVideos.push(...tvVideos)
      }

      if (varietyRes?.ok) {
        const varietyData = await varietyRes.json()
        const varietyVideos = (varietyData.items || []).map((item: any) => ({
          ...item,
          type: 'variety' as const
        }))
        allVideos.push(...varietyVideos)
      }

      // Filter videos with thumbnail
      allVideos = allVideos.filter(v => v.thumbnail && v.videoId)

      // Remove duplicates by videoId
      const seen = new Set<string>()
      allVideos = allVideos.filter(v => {
        if (seen.has(v.videoId)) {
          return false
        }
        seen.add(v.videoId)
        return true
      })

      // Limit to 6 items for homepage UX
      setVideos(allVideos.slice(0, 6))
    } catch (error) {
      console.error('Error fetching YouTube videos:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <SharedCarousel cardWidth={240} gap={12} maxVisible={6}>
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex-shrink-0 min-w-[240px] sm:min-w-[260px] bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="w-full h-32 bg-gray-100 animate-pulse" />
            <div className="p-3">
              <div className="h-4 bg-gray-100 rounded animate-pulse mb-2" />
              <div className="h-3 bg-gray-100 rounded animate-pulse w-2/3" />
            </div>
          </div>
        ))}
      </SharedCarousel>
    )
  }

  if (videos.length === 0) {
    return null
  }

  return (
    <SharedCarousel cardWidth={240} gap={12} maxVisible={6}>
      {videos.map((video, idx) => (
        <EntertainmentCard key={video.videoId || idx} video={video} />
      ))}
    </SharedCarousel>
  )
}

