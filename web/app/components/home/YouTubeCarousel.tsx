/**
 * YouTube Carousel Component - Right side of Row (col-span-5)
 * Reusable for both stock and tech videos
 */
'use client'

import { useState, useEffect } from 'react'
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

export function YouTubeCarousel({ category, title, viewMoreHref, limit = 3 }: YouTubeCarouselProps) {
  const [videos, setVideos] = useState<YouTubeVideo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchVideos()
  }, [category, limit])

  const fetchVideos = async () => {
    setLoading(true)
    try {
      let endpoint = ''
      if (category === 'stock') {
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

  // Don't render if no videos (empty sections are worse than missing sections)
  if (videos.length === 0) {
    return null
  }

  return (
    <StandardCard title={title} viewMoreHref={viewMoreHref}>

      {/* Carousel - Fixed height, horizontal scroll, max 3 videos */}
      <div className="flex-1 overflow-x-auto overflow-y-hidden pb-1 scrollbar-hide">
        <div className="flex gap-2 items-stretch h-[140px]">
          {videos.map((video) => (
            <div
              key={video.videoId}
              onClick={() => handleVideoClick(video)}
              className="flex-shrink-0 w-36 h-[140px] bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer flex flex-col"
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
  )
}

