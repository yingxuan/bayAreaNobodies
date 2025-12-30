/**
 * Gossip Carousel - (9) 北美八卦
 * 1point3acres top gossip posts - Horizontal carousel format
 */
'use client'

import { useState, useEffect } from 'react'
import { SharedCarousel } from './SharedCarousel'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type GossipCardProps = {
  post: {
    id?: number
    title: string
    title_cn?: string
    url?: string
    source?: string
    engagement?: number
    replies?: number
    created_at?: string
    summary?: string
    content?: string
    body?: string
    thumbnail_url?: string
  }
}

function GossipCard({ post }: GossipCardProps) {
  const handleClick = () => {
    if (post.url) {
      window.open(post.url, '_blank')
    }
  }

  const displayTitle = post.title_cn || post.title
  const sourceName = post.source === '1point3acres' ? '一亩三分地'
    : post.source === 'huaren' ? '华人网'
    : post.source === 'blind' ? 'Blind'
    : '热帖'
  
  // Fallback thumbnail (SVG data URI)
  const fallbackThumbnail = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEyOCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEyOCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2YjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 min-w-[240px] sm:min-w-[260px] bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start"
    >
      {/* Thumbnail/Icon */}
      <div className="relative w-full h-32 bg-gray-100">
        {post.thumbnail_url ? (
          <img
            src={post.thumbnail_url}
            alt={displayTitle}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.src = fallbackThumbnail
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-4xl">
            💬
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="p-3">
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-1.5">
          {displayTitle}
        </h4>
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>{sourceName}</span>
          <div className="flex items-center gap-1.5">
            {post.replies && (
              <span>💬 {post.replies}</span>
            )}
            {(post.engagement || post.replies) && (
              <span>🔥 {post.engagement || post.replies}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

type GossipCarouselProps = {
  hideTitle?: boolean
}

export function GossipCarousel({ hideTitle = false }: GossipCarouselProps = {}) {
  const [posts, setPosts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchGossip()
  }, [])

  const fetchGossip = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/feeds/gossip?limit=10`).catch(() => null)

      if (res?.ok) {
        const data = await res.json()
        const articles = data.articles || []
        
        // Filter for 1point3acres if possible, or use all
        const filtered = articles.filter((a: any) => 
          a.url?.includes('1point3acres') || 
          a.url?.includes('huaren') ||
          a.source_type === 'di_li' ||
          a.source_type === 'gossip'
        )
        
        // Map to include summary/content for preview - limit to 6 for UX
        const mapped = filtered.slice(0, 6).map((a: any) => ({
          ...a,
          summary: a.summary,
          content: a.cleaned_text || a.content,
          replies: a.views || a.saves || 0, // Use views/saves as engagement proxy
          engagement: a.views || a.saves || 0
        }))
        
        setPosts(mapped)
      }
    } catch (error) {
      console.error('Error fetching gossip:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <SharedCarousel cardWidth={240} gap={12} maxVisible={6}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex-shrink-0 min-w-[240px] sm:min-w-[260px] h-40 bg-gray-100 rounded-lg animate-pulse snap-start" />
        ))}
      </SharedCarousel>
    )
  }

  if (posts.length === 0) {
    return null
  }

  return (
    <SharedCarousel cardWidth={240} gap={12} maxVisible={6}>
      {posts.map((post, idx) => (
        <GossipCard key={post.id || post.url || idx} post={post} />
      ))}
    </SharedCarousel>
  )
}

