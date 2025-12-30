/**
 * Tech Video Cards - Right side of Tech Section (col-span-5)
 * Exactly 3 fixed-height video cards with 16:9 thumbnails
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type YouTubeVideo = {
  videoId: string
  title: string
  thumbnail: string
  duration?: string
  channelTitle?: string
  url?: string
}

export function TechVideoCards() {
  const [videos, setVideos] = useState<YouTubeVideo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/youtube-channels/tech?limit_per_channel=3`).catch(() => null)
      
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
        
        // Exactly 3 videos
        setVideos(videoList.slice(0, 3))
      }
    } catch (error) {
      console.error('Error fetching tech videos:', error)
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
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    )
  }

  if (videos.length === 0) {
    return null
  }

  return (
    <div className="flex flex-col">
      {/* Header - Reduced padding, match left side */}
      <div className="flex items-center justify-between mb-1.5 pb-1.5 border-b border-gray-200 min-h-[44px] flex-shrink-0">
        <h3 className="text-sm font-bold text-gray-900">📺 硅谷科技博客</h3>
        <Link href="/videos/tech" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap">
          更多 →
        </Link>
      </div>

      {/* Desktop: Vertical stack of 3 cards - Natural height, no flex-1 stretch */}
      <div className="hidden lg:flex flex-col gap-2">
        {videos.map((video) => (
          <div
            key={video.videoId}
            onClick={() => handleVideoClick(video)}
            className="flex gap-2 bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer h-[80px] flex-shrink-0"
          >
            {/* Thumbnail - 16:9 ratio, fixed width */}
            <div className="relative w-32 h-20 flex-shrink-0 bg-gray-100">
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
                <div className="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1 py-0.5 rounded">
                  {video.duration}
                </div>
              )}
            </div>
            
            {/* Content */}
            <div className="flex-1 p-2 flex flex-col min-w-0">
              <h4 className="text-xs font-semibold text-gray-900 line-clamp-2 mb-1">
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

      {/* Mobile: Horizontal carousel */}
      <div className="lg:hidden overflow-x-auto scrollbar-hide snap-x snap-mandatory pb-2">
        <div className="flex gap-3">
          {videos.map((video) => (
            <div
              key={video.videoId}
              onClick={() => handleVideoClick(video)}
              className="flex-shrink-0 min-w-[240px] bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start"
            >
              {/* Thumbnail - 16:9 ratio */}
              <div className="relative w-full aspect-video bg-gray-100">
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
              <div className="p-3">
                <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-1.5">
                  {video.title}
                </h4>
                {video.channelTitle && (
                  <div className="text-xs text-gray-500 line-clamp-1">
                    {video.channelTitle}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

