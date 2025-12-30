/**
 * Gossip Text List - 吃瓜
 * Vertical text-only list (NO carousel, NO images)
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type GossipItem = {
  id?: number
  title: string
  title_cn?: string
  url?: string
  source?: string
  created_at?: string
  published_at?: string
  fetched_at?: string
}

function parseTimeAgo(dateStr?: string): string {
  if (!dateStr) return ''
  
  try {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffDays > 0) {
      return `${diffDays}天前`
    } else if (diffHours > 0) {
      return `${diffHours}小时前`
    } else {
      const diffMins = Math.floor(diffMs / (1000 * 60))
      return diffMins > 0 ? `${diffMins}分钟前` : '刚刚'
    }
  } catch {
    return ''
  }
}

export function GossipTextList() {
  const [items, setItems] = useState<GossipItem[]>([])
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
        
        // Filter for relevant sources
        const filtered = articles.filter((a: any) => 
          a.url?.includes('1point3acres') || 
          a.url?.includes('huaren') ||
          a.source_type === 'di_li' ||
          a.source_type === 'gossip'
        )
        
        // Map to simplified structure - target 8, max 10
        const mapped = filtered.slice(0, 10).map((a: any) => ({
          id: a.id,
          title: a.title || '',
          title_cn: a.title_cn,
          url: a.url,
          source: a.source || a.source_type,
          created_at: a.created_at,
          published_at: a.published_at,
          fetched_at: a.fetched_at
        }))
        
        setItems(mapped)
      }
    } catch (error) {
      console.error('Error fetching gossip:', error)
    } finally {
      setLoading(false)
    }
  }

  const getSourceName = (source?: string) => {
    if (source === '1point3acres' || source === 'di_li') return '一亩三分地'
    if (source === 'huaren') return '华人网'
    if (source === 'blind') return 'Blind'
    return '热帖'
  }

  const getTimeAgo = (item: GossipItem) => {
    return parseTimeAgo(item.published_at || item.fetched_at || item.created_at)
  }

  if (loading) {
    return (
      <div className="space-y-0">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="py-2 border-b border-gray-100 last:border-0">
            <div className="h-4 bg-gray-100 rounded animate-pulse mb-1.5" />
            <div className="h-3 bg-gray-100 rounded animate-pulse w-2/3" />
          </div>
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <div className="text-xs text-gray-500 py-2">今天吃瓜较少，晚点再来</div>
    )
  }

  // Show empty state if less than 3 items
  if (items.length < 3) {
    return (
      <div className="text-xs text-gray-500 py-2">今天吃瓜较少，晚点再来</div>
    )
  }

  return (
    <div className="space-y-0">
      {items.slice(0, 8).map((item, idx) => {
        const displayTitle = item.title_cn || item.title
        const sourceName = getSourceName(item.source)
        const timeAgo = getTimeAgo(item)
        
        return (
          <Link
            key={item.id || item.url || idx}
            href={item.url || '#'}
            target={item.url ? '_blank' : undefined}
            rel={item.url ? 'noopener noreferrer' : undefined}
            className="block py-2 border-b border-gray-100 last:border-0 hover:bg-slate-50 transition-colors"
          >
            {/* Title - line-clamp-2 */}
            <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
              {displayTitle}
            </h4>
            
            {/* Meta line: source + time */}
            <div className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="whitespace-nowrap">{sourceName}</span>
              {timeAgo && (
                <>
                  <span>·</span>
                  <span className="whitespace-nowrap">{timeAgo}</span>
                </>
              )}
            </div>
          </Link>
        )
      })}
    </div>
  )
}

