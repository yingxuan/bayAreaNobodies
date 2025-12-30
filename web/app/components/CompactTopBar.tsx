/**
 * Compact Top Bar - Single line compressed indicators
 * Height ≤ 48px, inline display, no card border
 */
'use client'

import { useState, useEffect } from 'react'
import { fetchHotTopics, HotTopic } from '../lib/hotTopics'

export function CompactTopBar() {
  const [topics, setTopics] = useState<HotTopic[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadTopics = async () => {
      setLoading(true)
      try {
        const data = await fetchHotTopics()
        // Filter to only show: S&P 500, BTC, Gold, ARM, Powerball
        const filtered = data.filter(t => 
          t.id === 'market' || 
          t.id === 'btc' || 
          t.id === 'gold' || 
          t.id === 'jumbo_arm' || 
          t.id === 'lottery'
        )
        setTopics(filtered)
      } catch (error) {
        console.error('Error loading hot topics:', error)
        setTopics([])
      } finally {
        setLoading(false)
      }
    }
    
    loadTopics()
    
    // Refresh every 5 minutes
    const refreshInterval = setInterval(() => {
      loadTopics()
    }, 5 * 60 * 1000)
    
    return () => {
      clearInterval(refreshInterval)
    }
  }, [])

  if (loading) {
    return (
      <div className="h-12 bg-white border-b border-gray-200 flex items-center px-4 mb-4">
        <div className="flex items-center gap-4 text-sm text-gray-400">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="w-20 h-4 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  const hasMockData = topics.some(t => t.dataSource === 'mock')
  const trendIcon = (trend?: string) => {
    if (trend === 'up') return '↑'
    if (trend === 'down') return '↓'
    return ''
  }

  return (
    <div className="h-12 bg-white border-b border-gray-200 flex items-center justify-between px-4 mb-4">
      <div className="flex items-center gap-4 text-sm overflow-x-auto scrollbar-hide flex-1">
        {topics.map((topic) => {
          const trendColor = topic.trend === 'up' 
            ? 'text-green-600' 
            : topic.trend === 'down' 
            ? 'text-red-600' 
            : 'text-gray-600'
          
          return (
            <div key={topic.id} className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs">{topic.icon}</span>
              <span className="font-medium text-gray-700">{topic.label}</span>
              <span className="font-semibold text-gray-900">{topic.value}</span>
              {topic.change && topic.changePercent && (
                <span className={`text-xs font-medium ${trendColor}`}>
                  {trendIcon(topic.trend)}{topic.changePercent}
                </span>
              )}
            </div>
          )
        })}
      </div>
      
      {hasMockData && (
        <span className="text-xs text-yellow-600 px-2 py-0.5 bg-yellow-50 rounded flex-shrink-0 ml-4">
          Mock
        </span>
      )}
    </div>
  )
}

