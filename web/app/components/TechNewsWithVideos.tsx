/**
 * Tech News with YouTube Videos
 * Left: Tech News (40%) + Right: Tech Videos (60%)
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { generateWhatItMeans } from '../lib/techContent'
import { YouTubeVideoCarousel } from './YouTubeVideoCarousel'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type NewsItem = {
  title: string
  source?: string
  url?: string
}

export function TechNewsWithVideos() {
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
          // Only use Chinese conclusion/impact, not English title or fact description
          // Priority: generate "对你意味着什么" conclusion
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
          
          // Skip if no valid conclusion or if it's English
          if (!conclusion || /^[A-Z]/.test(conclusion) || conclusion.includes('发生了什么')) {
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
          
          return {
            title: conclusion,
            url: item.url || `/tech/${item.slug || ''}`
          }
        }).filter((item: any) => item !== null)
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
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8 text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-900">🧠 科技 & 新闻</h2>
      </div>

      {/* Vertical layout: Top (News) + Bottom (Videos) */}
      <div className="space-y-4">
        {/* Top: Tech News - 3 items max, conclusion-style */}
        <div>
          <div className="space-y-1.5">
            {newsItems.length > 0 ? (
              newsItems.map((item, idx) => (
                <Link
                  key={idx}
                  href={item.url || '#'}
                  className="block py-1.5 rounded hover:bg-gray-50 transition-colors"
                >
                  <h4 className="text-sm font-semibold text-gray-900 line-clamp-1">
                    {item.title}
                  </h4>
                </Link>
              ))
            ) : (
              <div className="text-sm text-gray-500">暂无新闻</div>
            )}
          </div>
          <div className="mt-2">
            <Link href="/tech" className="text-xs text-blue-600 hover:text-blue-700">
              查看更多 →
            </Link>
          </div>
        </div>

        {/* Bottom: Tech Videos - Extended content, only 硅谷101 */}
        <div className="pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-600 mb-3">深度解读</p>
          <YouTubeVideoCarousel category="tech" channelFilter="硅谷101" limit={6} />
        </div>
      </div>
    </div>
  )
}

