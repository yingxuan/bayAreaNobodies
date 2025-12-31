/**
 * Entertainment List - 追剧
 * Vertical stack of cards (max 4), NO carousel
 * Updated: 2025-12-30
 */
'use client'

import { useState, useEffect } from 'react'

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

type EntertainmentItemProps = {
  video: YouTubeVideo
}

function EntertainmentItem({ video }: EntertainmentItemProps) {
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
      className="flex gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-all cursor-pointer"
    >
      {/* Thumbnail - Fixed width, 16:9 aspect ratio */}
      <div className="relative w-40 flex-shrink-0 aspect-video bg-gray-100 rounded overflow-hidden">
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
      
      {/* Content - Title and source */}
      <div className="flex-1 min-w-0 flex flex-col justify-center">
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-1">
          {displayTitle}
        </h4>
        <div className="text-xs text-gray-600 line-clamp-1">
          {video.channelTitle}
        </div>
      </div>
    </div>
  )
}

export function EntertainmentList() {
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

      // Limit to max 4 items for homepage
      setVideos(allVideos.slice(0, 4))
    } catch (error) {
      console.error('Error fetching YouTube videos:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex gap-3 p-3 bg-white rounded-lg border border-gray-200">
            <div className="w-40 aspect-video bg-gray-100 rounded animate-pulse flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="h-4 bg-gray-100 rounded animate-pulse mb-2" />
              <div className="h-3 bg-gray-100 rounded animate-pulse w-2/3" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (videos.length === 0) {
    return (
      <div className="text-xs text-gray-500 py-4 text-center">暂无推荐，稍后再试</div>
    )
  }

  return (
    <div className="space-y-3">
      {videos.map((video, idx) => (
        <EntertainmentItem key={video.videoId || idx} video={video} />
      ))}
    </div>
  )
}

