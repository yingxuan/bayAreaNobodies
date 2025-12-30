/**
 * Tech Trends Module - 🧠 科技趋势 · 硅谷
 * Layout: Left (Context Panel) + Right (Video Carousel)
 * Tool-oriented, no marketing language
 */
'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type YouTubeVideo = {
  videoId: string
  title: string
  thumbnail: string
  publishedAt: string
  url?: string
}

type ContextData = {
  background: string
  points: string[]
  domains?: string[]
}

type TechTrendsData = {
  videos: YouTubeVideo[]
  context: ContextData
  loading: boolean
}

function formatRelativeTime(isoString: string): string {
  const now = new Date()
  const published = new Date(isoString)
  const diffMs = now.getTime() - published.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) {
    return '刚刚'
  } else if (diffMins < 60) {
    return `${diffMins} 分钟前`
  } else {
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) {
      return `${diffHours} 小时前`
    } else {
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays} 天前`
    }
  }
}

function VideoCard({ video }: { video: YouTubeVideo }) {
  const handleClick = () => {
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

  const fallbackThumbnail = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iIzFmMjkzNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 w-56 bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer"
    >
      {/* Thumbnail */}
      <div className="relative w-full h-32 bg-gray-100">
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
      </div>
      
      {/* Content */}
      <div className="p-3">
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-1">
          {video.title}
        </h4>
        <div className="text-xs text-gray-500">
          {formatRelativeTime(video.publishedAt)}
        </div>
      </div>
    </div>
  )
}

export function TechTrends() {
  const [data, setData] = useState<TechTrendsData>({
    videos: [],
    context: {
      background: '',
      points: []
    },
    loading: true
  })

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setData(prev => ({ ...prev, loading: true }))
    try {
      const [videosRes, contextRes] = await Promise.all([
        fetch(`${API_URL}/tech-trends/channel?channel=硅谷101&limit=5`).catch(() => null),
        fetch(`${API_URL}/tech-trends/context`).catch(() => null)
      ])

      let videos: YouTubeVideo[] = []
      let context: ContextData = {
        background: '硅谷科技公司近期动态涉及AI芯片、云计算和人才市场变化。',
        points: [
          'AI芯片竞争持续，NVIDIA、AMD等公司发布新产品',
          '云计算服务价格调整，影响企业技术选型',
          '湾区科技公司招聘和裁员情况出现波动'
        ],
        domains: ['AI芯片', '云计算', '人才市场']
      }

      if (videosRes?.ok) {
        const videosData = await videosRes.json()
        videos = (videosData.items || []).map((item: any) => ({
          videoId: item.videoId,
          title: item.title,
          thumbnail: item.thumbnail,
          publishedAt: item.publishedAt,
          url: item.url || `https://www.youtube.com/watch?v=${item.videoId}`
        }))
      }

      if (contextRes?.ok) {
        const contextData = await contextRes.json()
        context = contextData.context || context
      }

      setData({
        videos,
        context,
        loading: false
      })
    } catch (error) {
      console.error('Error fetching tech trends:', error)
      setData(prev => ({ ...prev, loading: false }))
    }
  }

  if (data.loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🧠 科技趋势 · 硅谷</h2>
        <div className="text-center py-8 text-gray-500">加载中...</div>
      </div>
    )
  }

  if (data.videos.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-900">🧠 科技趋势 · 硅谷</h2>
        {/* Optional subtitle - can be removed if visually redundant */}
        <p className="text-sm text-gray-500 mt-1">数据来源：YouTube · 硅谷101</p>
      </div>

      {/* Desktop: Left (Context) + Right (Videos) */}
      <div className="lg:grid lg:grid-cols-5 lg:gap-6">
        {/* Left: Context Panel (40%) */}
        <div className="lg:col-span-2 mb-4 lg:mb-0">
          <div className="space-y-3">
            {/* Background statement */}
            {data.context.background && (
              <p className="text-sm text-gray-700 leading-relaxed">
                {data.context.background}
              </p>
            )}

            {/* Key points */}
            {data.context.points && data.context.points.length > 0 && (
              <ul className="space-y-2">
                {data.context.points.map((point, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start">
                    <span className="text-gray-400 mr-2">•</span>
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            )}

            {/* Optional: Domains */}
            {data.context.domains && data.context.domains.length > 0 && (
              <div className="pt-2 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-1">涉及领域：</p>
                <div className="flex flex-wrap gap-2">
                  {data.context.domains.map((domain, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                    >
                      {domain}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Video Carousel (60%) */}
        <div className="lg:col-span-3">
          <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
            {data.videos.map((video) => (
              <VideoCard key={video.videoId} video={video} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

