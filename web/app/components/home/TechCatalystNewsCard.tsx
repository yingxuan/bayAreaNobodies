/**
 * Tech Catalyst News Card - Left side of Tech Row (col-span-7)
 * Displays: 3-4 Chinese conclusion-type news items that affect tech stocks
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { generateWhatItMeans } from '../../lib/techContent'
import { extractChineseConclusion } from '../../lib/i18nZh'
import { StandardCard } from './StandardCard'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type NewsItem = {
  title: string
  url?: string
  source?: string
  timeAgo?: string
  affectedTickers?: string[]
}

export function TechCatalystNewsCard() {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNews()
  }, [])

  const fetchNews = async () => {
    setLoading(true)
    try {
      // Fetch tech news (limit 4 for compact display)
      const techRes = await fetch(`${API_URL}/tech/trending?source=hn&limit=4`).catch(() => null)
      
      if (techRes?.ok) {
        const techData = await techRes.json()
        
        const items = (techData.items || []).slice(0, 4).map((item: any) => {
          // Only use Chinese conclusion/impact, not English title or fact description
          let conclusion = ''
          
          // Try to generate conclusion from title and tags
          if (item.title && item.tags) {
            const titleCN = item.title_cn || item.title
            conclusion = generateWhatItMeans(item.title, item.tags || [], titleCN)
          }
          
          // Fallback: use title_cn if it's already a conclusion (not English, not fact description)
          if (!conclusion && item.title_cn) {
            const titleCN = item.title_cn
            // Skip if it's English or fact description
            if (!/^[A-Z]/.test(titleCN) && !titleCN.includes('发生了什么')) {
              // Extract "对你意味着" part if exists
              const match = titleCN.match(/对你意味着[：:](.+)/)
              if (match) {
                conclusion = match[1].trim()
              } else {
                conclusion = titleCN
              }
            }
          }
          
          // Try extractChineseConclusion as last resort
          if (!conclusion) {
            conclusion = extractChineseConclusion(item.title, item.title_cn)
          }
          
          // Skip if no valid conclusion or if it's English (and not in brackets)
          if (!conclusion || (/^[A-Z]/.test(conclusion) && !conclusion.startsWith('【'))) {
            return null
          }
          
          // Clean up: remove any redundant patterns
          conclusion = conclusion
            .replace(/对你意味着[：:].*$/, '')
            .replace(/→.*$/, '')
            .trim()
          
          if (conclusion.length === 0) {
            return null
          }
          
          // Extract affected tickers from tags or title
          const affectedTickers: string[] = []
          const tickerMap: Record<string, string> = {
            'google': 'GOOG',
            'alphabet': 'GOOG',
            'openai': 'MSFT', // OpenAI is backed by Microsoft
            'meta': 'META',
            'facebook': 'META',
            'microsoft': 'MSFT',
            'amazon': 'AMZN',
            'aws': 'AMZN',
            'nvidia': 'NVDA',
            'apple': 'AAPL',
            'amd': 'AMD',
            'tsla': 'TSLA',
            'tesla': 'TSLA',
          }
          
          const titleLower = (item.title || '').toLowerCase()
          const tagsLower = (item.tags || []).map((t: string) => t.toLowerCase())
          
          for (const [key, ticker] of Object.entries(tickerMap)) {
            if (titleLower.includes(key) || tagsLower.includes(key)) {
              if (!affectedTickers.includes(ticker)) {
                affectedTickers.push(ticker)
              }
            }
          }
          
          return {
            title: conclusion,
            url: item.url || `/tech/${item.slug || ''}`,
            source: item.source || 'Hacker News',
            timeAgo: item.timeAgo || '',
            affectedTickers: affectedTickers.slice(0, 3) // Max 3 tickers
          }
        }).filter((item: any) => item !== null) // Filter out nulls
        
        setNewsItems(items.slice(0, 3)) // Max 3 items
      }
    } catch (error) {
      console.error('Error fetching tech news:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 h-full flex items-center justify-center">
        <div className="text-xs text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <StandardCard title="🧠 影响科技股的要闻" viewMoreHref="/tech">
      {/* News List - Text only, no thumbnails */}
      <div className="space-y-0">
        {newsItems.length > 0 ? (
          newsItems.map((item, idx) => (
            <Link
              key={idx}
              href={item.url || '#'}
              className={`block py-1.5 ${idx < newsItems.length - 1 ? 'border-b border-gray-100' : ''} hover:bg-gray-50 transition-colors`}
            >
              {/* Title - Bold, max 2 lines */}
              <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-0.5">
                {item.title}
              </h4>
              
              {/* Source + Time + Tickers */}
              <div className="flex items-center gap-2 text-xs text-gray-500">
                {item.source && (
                  <span>{item.source}</span>
                )}
                {item.timeAgo && (
                  <span>· {item.timeAgo}</span>
                )}
                {item.affectedTickers && item.affectedTickers.length > 0 && (
                  <div className="flex items-center gap-1 ml-auto">
                    {item.affectedTickers.map((ticker) => (
                      <span
                        key={ticker}
                        className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium"
                      >
                        {ticker}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </Link>
          ))
        ) : (
          <div className="text-xs text-gray-500 py-2">暂无新闻</div>
        )}
      </div>
    </StandardCard>
  )
}

