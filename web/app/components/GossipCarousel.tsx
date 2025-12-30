/**
 * Gossip Carousel - (9) 北美八卦
 * 1point3acres top gossip posts
 */
'use client'

import { useState, useEffect } from 'react'
import { CarouselSection } from './CarouselSection'

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
  
  // Extract preview text (first 1-2 lines of content)
  const preview = post.summary || post.content || post.body || ''
  const previewLines = preview
    .split('\n')
    .filter(line => line.trim())
    .slice(0, 2)
    .join(' ')
    .substring(0, 100)
    .trim()

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 w-72 bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-all cursor-pointer"
    >
      <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-2">
        {displayTitle}
      </h4>
      
      {/* Preview text */}
      {previewLines && (
        <p className="text-xs text-gray-600 line-clamp-2 mb-2">
          {previewLines}
        </p>
      )}
      
      {/* Engagement info */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{sourceName}</span>
        <div className="flex items-center gap-2">
          {post.replies && (
            <span>💬 {post.replies}</span>
          )}
          {(post.engagement || post.replies) && (
            <span>🔥 {post.engagement || post.replies}</span>
          )}
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
      const res = await fetch(`${API_URL}/feeds/gossip?limit=12`).catch(() => null)

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
        
        // Map to include summary/content for preview
        const mapped = filtered.slice(0, 12).map((a: any) => ({
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
      <CarouselSection title={hideTitle ? "" : "🗣 北美八卦"} viewMoreHref="/gossip">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex-shrink-0 w-64 h-24 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </CarouselSection>
    )
  }

  if (posts.length === 0) {
    return null
  }

  return (
    <CarouselSection
      title={hideTitle ? "" : "🗣 北美八卦"}
      viewMoreHref="/gossip"
    >
      {posts.map((post, idx) => (
        <GossipCard key={post.id || post.url || idx} post={post} />
      ))}
    </CarouselSection>
  )
}

