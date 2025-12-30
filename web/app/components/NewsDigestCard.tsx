/**
 * News Digest Card - (3) 科技行业 & 美国经济新闻
 * High-density, Chinese-first, concise news
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { generateConcreteTitle, generateWhatItMeans } from '../lib/techContent'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type NewsItem = {
  title: string
  impact: string
  url?: string
}

export function NewsDigestCard() {
  const [newsItems, setNewsItems] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNews()
  }, [])

  const fetchNews = async () => {
    setLoading(true)
    try {
      // Fetch tech news (limit 3 for compact display)
      const techRes = await fetch(`${API_URL}/tech/trending?source=hn&limit=3`).catch(() => null)
      
      if (techRes?.ok) {
        const techData = await techRes.json()
        
        const items = (techData.items || []).slice(0, 3).map((item: any) => {
          const title = item.title_cn || generateConcreteTitle(item.title || '', item.tags || []) || '科技动态'
          // Generate impact directly (no "发生了什么" template)
          // Use title as whatHappened for generateWhatItMeans (since we don't show "发生了什么")
          const impact = item.impact_cn || generateWhatItMeans(item.title || '', item.tags || [], title) || '可能影响工作方式或职业路径'
          
          return {
            title,
            impact,
            url: item.url || `/tech/${item.slug || ''}`
          }
        })
        setNewsItems(items)
      }
    } catch (error) {
      console.error('Error fetching news:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
        <div className="text-sm text-gray-500">加载中...</div>
      </div>
    )
  }

  if (newsItems.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-3 border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-bold text-gray-900">📰 科技 & 经济</h3>
        <Link href="/tech" className="text-xs text-blue-600">更多 →</Link>
      </div>
      
      <div className="space-y-2">
        {newsItems.map((item, idx) => (
          <div key={idx} className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h4 className="text-xs font-semibold text-gray-900 line-clamp-1 mb-0.5">{item.title}</h4>
              <p className="text-xs text-blue-700 font-medium">→ {item.impact}</p>
            </div>
            {item.url && (
              <Link href={item.url} className="text-xs text-blue-600 flex-shrink-0">详情</Link>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

