'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { generateChineseTitle } from '../lib/i18n'
import { generateConcreteTitle, generateWhatHappened, generateWhatItMeans, generateWhatYouCanDo } from '../lib/techContent'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function formatRelativeTime(isoString: string): string {
  const now = new Date()
  const updated = new Date(isoString)
  const diffMs = now.getTime() - updated.getTime()
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

type TechItem = {
  id: string
  title: string
  url: string
  score?: number
  comments?: number
  author?: string
  createdAt?: string
  tags: string[]
  summary?: string
}

type TechTrendingResponse = {
  source: string
  updatedAt: string
  dataSource: 'live' | 'mock'
  items: TechItem[]
}

export function TechRadar() {
  const [data, setData] = useState<TechTrendingResponse>({
    source: 'hn',
    updatedAt: new Date().toISOString(),
    dataSource: 'mock',
    items: []
  })
  const [loading, setLoading] = useState(true)
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  useEffect(() => {
    const fetchTechTrending = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_URL}/tech/trending?source=hn&limit=3`, {
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache'
          }
        })
        
        if (res.ok) {
          const result = await res.json()
          setData(result)
        } else {
          console.error('Failed to fetch tech trending:', res.status)
        }
      } catch (error) {
        console.error('Error fetching tech trending:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTechTrending()
  }, [])

  // Sort by score to find the hottest one
  const sortedItems = [...data.items].sort((a, b) => (b.score || 0) - (a.score || 0))
  const topScore = sortedItems[0]?.score || 0

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-900 mb-1">🧠 科技圈新动向</h2>
          <p className="text-sm text-gray-500">今天值得你花 2 分钟知道的 3 件事</p>
        </div>
        <div className="text-center py-8 text-gray-500">加载中...</div>
      </div>
    )
  }

  if (data.items.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <div className="mb-4">
          <h2 className="text-xl font-bold text-gray-900 mb-1">🧠 科技圈新动向</h2>
          <p className="text-sm text-gray-500">今天值得你花 2 分钟知道的 3 件事</p>
        </div>
        <div className="text-center py-8 text-gray-500">
          <p className="mb-2">暂无数据</p>
          <Link href="/tech" className="text-sm text-blue-600 hover:text-blue-700">
            查看科技页面 →
          </Link>
        </div>
      </div>
    )
  }

  const tagMap: Record<string, string> = {
    'AI': 'AI',
    'Chips': '芯片',
    'BigTech': '大厂',
    'Infra': '基础设施',
    'Security': '安全',
    'Career': '职场',
    'OpenSource': '开源',
    'Tech': '科技',
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
      {/* Header */}
      <div className="mb-4">
        <h2 className="text-xl font-bold text-gray-900 mb-1">🧠 科技圈新动向</h2>
        <p className="text-sm text-gray-500">今天值得你花 2 分钟知道的 3 件事</p>
      </div>

      {/* Top 3 Cards */}
      <div className="space-y-3">
        {sortedItems.map((item, index) => {
          const isTopItem = item.score === topScore && topScore > 0
          const isExpanded = expandedItems.has(item.id)
          const concreteTitle = generateConcreteTitle(item.title, item.tags)
          const whatHappened = generateWhatHappened(item.title, item.tags, concreteTitle)
          const whatItMeans = generateWhatItMeans(item.title, item.tags, whatHappened)
          const whatYouCanDo = generateWhatYouCanDo(item.title, item.tags, whatHappened)
          
          const toggleExpand = (e: React.MouseEvent) => {
            e.preventDefault()
            e.stopPropagation()
            const newExpanded = new Set(expandedItems)
            if (isExpanded) {
              newExpanded.delete(item.id)
            } else {
              newExpanded.add(item.id)
            }
            setExpandedItems(newExpanded)
          }
          
          return (
            <div
              key={item.id}
              className={`block rounded-lg hover:shadow-md transition-all ${
                isTopItem 
                  ? 'border-2 border-orange-300 bg-orange-50/30' 
                  : 'border border-gray-200'
              }`}
            >
              {/* Collapsed State - Only Title + What It Means */}
              <div 
                className="p-4 cursor-pointer"
                onClick={toggleExpand}
              >
                {/* Category Tags */}
                {item.tags.length > 0 && (
                  <div className="flex gap-2 mb-2">
                    {item.tags.slice(0, 2).map((tag) => {
                      const cnTag = tagMap[tag] || tag
                      return (
                        <span
                          key={tag}
                          className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded"
                        >
                          {cnTag}
                        </span>
                      )
                    })}
                    {isTopItem && (
                      <span className="px-2 py-0.5 text-xs bg-orange-100 text-orange-700 rounded font-medium">
                        🔥 今日重点
                      </span>
                    )}
                  </div>
                )}

                {/* Concrete Title - Specific Entity + Event */}
                <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 text-base">
                  {concreteTitle}
                </h3>

                {/* What It Means - Core conclusion only */}
                <p className="text-sm text-blue-700 font-medium">
                  → 对你意味着：{whatItMeans}
                </p>

                {/* Expand Indicator */}
                <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    {item.score !== undefined && (
                      <span>🔥 {item.score}</span>
                    )}
                    {item.author && (
                      <span>by {item.author}</span>
                    )}
                    {data.dataSource === 'mock' && (
                      <span className="text-yellow-600">Mock</span>
                    )}
                  </div>
                  <span className="text-xs text-gray-400">
                    {isExpanded ? '收起' : '展开详情'}
                  </span>
                </div>
              </div>

              {/* Expanded State - What Happened + What You Can Do */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  {/* What Happened - Factual details only, no repetition of title */}
                  {whatHappened && (
                    <div className="pt-3 mb-3">
                      <p className="text-xs font-medium text-gray-500 mb-1">发生了什么</p>
                      <p className="text-sm text-gray-700 leading-relaxed">
                        {whatHappened}
                      </p>
                    </div>
                  )}

                  {/* What You Can Do - Specific, actionable */}
                  {whatYouCanDo && (
                    <div className="mb-3">
                      <p className="text-xs font-medium text-gray-500 mb-1">你现在可以</p>
                      <p className="text-sm text-green-700 leading-relaxed">
                        {whatYouCanDo}
                      </p>
                    </div>
                  )}

                  {/* External Link */}
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700"
                    onClick={(e) => e.stopPropagation()}
                  >
                    查看原文 →
                  </a>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* View More */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <Link
          href="/tech?source=hn"
          className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
        >
          查看更多 →
        </Link>
      </div>
    </div>
  )
}
