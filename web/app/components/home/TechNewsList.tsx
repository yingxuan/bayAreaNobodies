/**
 * Tech News List - Left side of Tech Section (col-span-7)
 * Clean text-only list without card wrapper
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type NewsItem = {
  title: string
  url?: string
  source?: string
  timeAgo?: string
  affectedTickers?: string[]
  category?: string
}

export function TechNewsList() {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNews()
  }, [])

  const fetchNews = async () => {
    setLoading(true)
    try {
      // Fetch AI news from aggregated sources (web-wide, not just HN)
      // Request 5 items to match right side height
      const aiNewsRes = await fetch(`${API_URL}/tech/ai-news?limit=5`).catch(() => null)
      
      if (aiNewsRes?.ok) {
        const aiNewsData = await aiNewsRes.json()
        
        // Process items - they're already deduplicated and ranked by backend
        const processedItems: NewsItem[] = []
        
        for (const item of aiNewsData.items || []) {
          const displayTitle = (item.title || '').trim()
          
          // Skip if no valid title
          if (!displayTitle || displayTitle.length === 0) {
            continue
          }
          
          processedItems.push({
            title: displayTitle,
            url: item.url || '#',
            source: item.source || 'Unknown',
            timeAgo: item.timeAgo || '',
            affectedTickers: item.affectedTickers || [],
            category: item.category || undefined
          })
        }
        
        // Display exactly 5 items to match right side height
        const displayCount = Math.min(processedItems.length, 5)
        setNewsItems(processedItems.slice(0, displayCount))
      }
    } catch (error) {
      console.error('Error fetching AI news:', error)
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
            <div key={i} className="h-[51px] bg-gray-100 rounded animate-pulse mb-0" />
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
        <div className="text-xs text-gray-500 py-2">今日新闻较少，稍后再试</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header - Reduced padding */}
      <div className="flex items-center justify-between mb-1.5 pb-1.5 border-b border-gray-200 min-h-[44px] flex-shrink-0">
        <h3 className="text-sm font-bold text-gray-900">🔥 今日热点</h3>
        <Link href="/tech" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap">
          更多 →
        </Link>
      </div>

      {/* News List - Dense, text-only, flex-1 */}
      <div className="flex-1 space-y-0">
        {newsItems.length > 0 ? (
          newsItems.map((item, idx) => (
            <Link
              key={idx}
              href={item.url || '#'}
              className={`block py-1.5 ${idx < newsItems.length - 1 ? 'border-b border-slate-100' : ''} hover:bg-gray-50 transition-colors`}
            >
              {/* Title - line-clamp-2, font-medium */}
              <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-0.5">
                {item.title}
              </h4>
              
              {/* Meta row: Source + Time + Tag */}
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                {item.source && (
                  <span className="whitespace-nowrap">{item.source}</span>
                )}
                {item.timeAgo && (
                  <span className="whitespace-nowrap">· {item.timeAgo}</span>
                )}
                {/* Tag on the right - prefer ticker, then category, fallback to source */}
                <div className="flex items-center gap-1 ml-auto">
                  {item.affectedTickers && item.affectedTickers.length > 0 ? (
                    <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium whitespace-nowrap">
                      {item.affectedTickers[0]}
                    </span>
                  ) : item.category ? (
                    <span className="px-1.5 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium whitespace-nowrap">
                      {item.category}
                    </span>
                  ) : item.source ? (
                    <span className="px-1.5 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium whitespace-nowrap">
                      {item.source}
                    </span>
                  ) : null}
                </div>
              </div>
            </Link>
          ))
        ) : (
          <div className="text-xs text-gray-500 py-2">暂无新闻</div>
        )}
      </div>
    </div>
  )
}

