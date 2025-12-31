/**
 * Industry News List - Chinese-first summary cards
 * Shows "今天湾区码农该知道的 3–5 件事"
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type NewsItem = {
  summary_zh: string
  why_it_matters_zh: string
  tags: string[]
  original_url: string
  source: string
  time_ago: string
  published_at?: string
  score?: number
  title?: string  // Original English title (optional, shown very small)
  judged?: boolean  // Flag indicating judgment pipeline
  reason?: string  // Why this item was selected
}

type NewsResponse = {
  overall_brief_zh?: string
  items: NewsItem[]
  total: number
}

export function TechNewsList() {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([])
  const [overallBrief, setOverallBrief] = useState<string>("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNews()
  }, [])

  const fetchNews = async () => {
    setLoading(true)
    try {
      // Fetch industry news from new endpoint
      const res = await fetch(`${API_URL}/news/industry?limit=5`).catch(() => null)
      
      if (res?.ok) {
        const data: NewsResponse = await res.json()
        // Filter items that have summary_zh or why_it_matters_zh
        // Also accept items with title as fallback
        const items = (data.items || []).filter((item: NewsItem) => 
          (item.summary_zh && item.summary_zh.trim()) || 
          (item.why_it_matters_zh && item.why_it_matters_zh.trim()) ||
          item.title
        )
        setNewsItems(items)
        setOverallBrief(data.overall_brief_zh || "")
      }
    } catch (error) {
      console.error('Error fetching industry news:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between mb-1.5 pb-1.5 border-b border-gray-200 min-h-[44px] flex-shrink-0">
          <h3 className="text-sm font-bold text-gray-900">🔥 今日热点</h3>
        </div>
        <div className="flex-1 space-y-0">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-[70px] bg-gray-100 rounded animate-pulse mb-0" />
          ))}
        </div>
      </div>
    )
  }

  if (newsItems.length === 0) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between mb-1.5 pb-1.5 border-b border-gray-200 min-h-[44px] flex-shrink-0">
          <h3 className="text-sm font-bold text-gray-900">🔥 今日热点</h3>
        </div>
        <div className="text-xs text-gray-500 py-2">今天没有重要行业新闻</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-1.5 pb-1.5 border-b border-gray-200 min-h-[44px] flex-shrink-0">
        <h3 className="text-sm font-bold text-gray-900">🔥 今日热点</h3>
        <div className="flex items-center gap-2">
          {/* Dev badge: show judged/cache/mock status */}
          {process.env.NODE_ENV === 'development' && newsItems.length > 0 && (
            <span className="text-[10px] text-gray-400 px-1.5 py-0.5 bg-gray-100 rounded">
              {newsItems[0].judged ? 'judged' : 'cache'}
            </span>
          )}
          <Link href="/tech" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap">
            更多 →
          </Link>
        </div>
      </div>
      
      {/* Overall brief (if available) */}
      {overallBrief && (
        <div className="mb-2 px-2 py-1.5 bg-blue-50 rounded text-xs text-gray-700 border-l-2 border-blue-400">
          {overallBrief}
        </div>
      )}

      {/* News List - Chinese-first summary cards */}
      <div className="flex-1 space-y-0">
        {newsItems.map((item, idx) => (
          <a
            key={idx}
            href={item.original_url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className={`block py-2.5 ${idx < newsItems.length - 1 ? 'border-b border-gray-100' : ''} hover:bg-gray-50 transition-colors`}
          >
            {/* Summary (bold, line-clamp-2) - ALWAYS show summary_zh first, fallback to title */}
            <h4 className="text-sm font-bold text-gray-900 line-clamp-2 mb-1">
              {item.summary_zh && item.summary_zh.trim() 
                ? item.summary_zh 
                : item.title || "无标题"}
            </h4>
            
            {/* Why it matters (muted, line-clamp-1) - Show if available */}
            {item.why_it_matters_zh && item.why_it_matters_zh.trim() && (
              <p className="text-xs text-gray-600 line-clamp-1 mb-1.5">
                {item.why_it_matters_zh}
              </p>
            )}
            
            {/* Original English title (very small, muted, shown on hover) - Only if different from summary */}
            {item.title && item.title !== item.summary_zh && (
              <p className="text-[10px] text-gray-400 line-clamp-1 mb-0.5 opacity-0 hover:opacity-100 transition-opacity">
                {item.title}
              </p>
            )}
            
            {/* Tags + Source + Time */}
            <div className="flex items-center gap-1.5 flex-wrap">
              {/* Tags pills (max 3) */}
              {item.tags && item.tags.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap">
                  {item.tags.slice(0, 3).map((tag, tagIdx) => (
                    <span
                      key={tagIdx}
                      className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium whitespace-nowrap"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              
              {/* Source + Time */}
              <div className="flex items-center gap-1 text-xs text-gray-500 ml-auto">
                {item.source && (
                  <span className="whitespace-nowrap">{item.source}</span>
                )}
                {item.time_ago && (
                  <>
                    <span className="text-gray-400">·</span>
                    <span className="whitespace-nowrap">{item.time_ago}</span>
                  </>
                )}
              </div>
            </div>
          </a>
        ))}
      </div>
    </div>
  )
}
