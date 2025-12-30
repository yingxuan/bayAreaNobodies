/**
 * Breaking News Ticker - Shows 1-2 breaking stock market headlines
 * Uses existing news sources (no new APIs)
 */
'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type NewsItem = {
  headline: string
  url?: string
  source?: string
}

export function BreakingNewsTicker() {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBreakingNews()
  }, [])

  const fetchBreakingNews = async () => {
    setLoading(true)
    try {
      // Use existing stock news API for major indices (SPY represents market)
      // Fetch news for SPY (S&P 500) as market indicator - last 6 hours for breaking news
      const res = await fetch(`${API_URL}/stocks/news?ticker=SPY&range_hours=6`).catch(() => null)
      
      if (res?.ok) {
        const newsList = await res.json()
        // newsList is already an array of StockNewsItem
        const formatted = (Array.isArray(newsList) ? newsList : []).slice(0, 2).map((item: any) => ({
          headline: item.headline || item.title || '',
          url: item.url || item.link || '',
          source: item.source || 'Market News'
        })).filter((item: NewsItem) => item.headline && item.headline.length > 0)
        
        setNewsItems(formatted)
      }
    } catch (error) {
      console.error('Error fetching breaking news:', error)
    } finally {
      setLoading(false)
    }
  }

  // Don't render if no news or loading
  if (loading || newsItems.length === 0) {
    return null
  }

  return (
    <div className="px-3 sm:px-4 py-1.5 border-t border-gray-100 bg-gray-50/50">
      {/* Desktop: Full width with label */}
      <div className="hidden sm:flex items-center gap-2 text-xs">
        <span className="text-red-600 font-bold flex-shrink-0">🔥 股市 Breaking News</span>
        <div className="flex items-center gap-2 flex-1 min-w-0">
          {newsItems.map((item, idx) => (
            <div key={idx} className="flex items-center gap-2 flex-shrink-0">
              {item.url ? (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-700 hover:text-blue-600 line-clamp-1 truncate max-w-md"
                  title={item.headline}
                >
                  {item.headline}
                </a>
              ) : (
                <span className="text-gray-700 line-clamp-1 truncate max-w-md" title={item.headline}>
                  {item.headline}
                </span>
              )}
              {idx < newsItems.length - 1 && (
                <span className="text-gray-400 flex-shrink-0">•</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Mobile: Single line ticker with overflow hidden */}
      <div className="sm:hidden overflow-hidden">
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-red-600 font-bold flex-shrink-0">🔥</span>
          <div className="flex items-center gap-1.5 flex-1 min-w-0 overflow-hidden">
            {newsItems.map((item, idx) => (
              <div key={idx} className="flex items-center gap-1.5 flex-shrink-0">
                {item.url ? (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-700 hover:text-blue-600 line-clamp-1 truncate"
                    title={item.headline}
                  >
                    {item.headline}
                  </a>
                ) : (
                  <span className="text-gray-700 line-clamp-1 truncate" title={item.headline}>
                    {item.headline}
                  </span>
                )}
                {idx < newsItems.length - 1 && (
                  <span className="text-gray-400 flex-shrink-0">•</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

