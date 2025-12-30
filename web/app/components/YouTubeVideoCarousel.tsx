/**
 * YouTube Video Carousel Component
 * Reusable component for displaying YouTube videos in a horizontal carousel
 */
'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type YouTubeVideo = {
  videoId: string
  title: string
  thumbnail: string
  duration?: string
  channelTitle?: string
  url?: string
}

type YouTubeVideoCarouselProps = {
  category: 'stock' | 'tech'
  limit?: number
  className?: string
  compact?: boolean
  channelFilter?: string
}

export function YouTubeVideoCarousel({ category, limit, className = '', compact = false, channelFilter }: YouTubeVideoCarouselProps) {
  const [videos, setVideos] = useState<YouTubeVideo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchVideos()
  }, [category, limit, channelFilter])

  const fetchVideos = async () => {
    setLoading(true)
    try {
      let endpoint = ''
      if (category === 'stock') {
        endpoint = `/youtube-channels/stock?limit_per_channel=1`
      } else {
        // For tech, filter by channel if specified
        if (channelFilter) {
          endpoint = `/youtube-channels/tech?channels=${encodeURIComponent(channelFilter)}&limit_per_channel=3`
        } else {
          endpoint = `/youtube-channels/tech?limit_per_channel=3`
        }
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
        
        // Filter by channel if specified
        if (channelFilter) {
          videoList = videoList.filter((v: any) => 
            v.channelTitle?.includes(channelFilter)
          )
        }
        
        if (limit) {
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
    
    // Mobile: try to open YouTube app, fallback to web
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

  if (loading) {
    const cardWidth = compact ? 'w-36' : 'w-48'
    const cardHeight = compact ? 'h-24' : 'h-32'
    return (
      <div className={`flex gap-4 overflow-x-auto pb-2 scrollbar-hide ${className}`}>
        {[1, 2, 3].map((i) => (
          <div key={i} className={`flex-shrink-0 ${cardWidth} ${cardHeight} bg-gray-100 rounded-lg animate-pulse`} />
        ))}
      </div>
    )
  }

  if (videos.length === 0) {
    return null
  }

  const fallbackThumbnail = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iIzFmMjkzNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'

  const cardWidth = compact ? 'w-36' : 'w-48'
  const thumbnailHeight = compact ? 'h-20' : 'h-28'
  const textSize = compact ? 'text-xs' : 'text-xs'

  return (
    <div className={`flex gap-3 overflow-x-auto pb-2 scrollbar-hide ${className}`}>
      {videos.map((video) => (
        <div
          key={video.videoId}
          onClick={() => handleVideoClick(video)}
          className={`flex-shrink-0 ${cardWidth} bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer`}
        >
          {/* Thumbnail */}
          <div className={`relative w-full ${thumbnailHeight} bg-gray-100`}>
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
          
          {/* Content */}
          <div className={compact ? 'p-1.5' : 'p-2'}>
            <h4 className={`${textSize} font-semibold text-gray-900 ${compact ? 'line-clamp-1' : 'line-clamp-2'} ${compact ? '' : 'mb-1'}`}>
              {video.title}
            </h4>
            {!compact && video.channelTitle && (
              <div className="text-xs text-gray-500 line-clamp-1">
                {video.channelTitle}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

