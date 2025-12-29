'use client'

import { useState, useEffect } from 'react'
import { HotTopicCard } from './HotTopicCard'
import { fetchHotTopics, HotTopic } from '../lib/hotTopics'
import { getTechItems } from '../lib/techNews'

export function TodayCommandBar() {
  const [topics, setTopics] = useState<HotTopic[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadTopics = async () => {
      setLoading(true)
      try {
        const data = await fetchHotTopics()
        
        // Check if there's breaking tech news or high-engagement tech news
        try {
          const techItems = await getTechItems(1)
          if (techItems.length > 0) {
            const techItem = techItems[0]
            // Show tech card if it's breaking or has high engagement
            if (techItem.isBreaking || (techItem.metrics?.points && techItem.metrics.points > 1000)) {
              // Add tech topic as 6th item (will be shown conditionally)
              const techTopic: HotTopic = {
                id: 'tech',
                type: 'market', // Reuse type
                icon: '🧠',
                label: 'Tech',
                value: techItem.title.substring(0, 30) + '...',
                change: undefined,
                changePercent: undefined,
                trend: 'neutral',
                href: `/tech/${techItem.slug}`,
                dataSource: 'api'
              }
              // For now, keep 5 topics (tech is shown in TodayBrief instead)
              // Future: could replace one topic or show 6 on larger screens
            }
          }
        } catch (error) {
          console.error('Error checking tech news:', error)
        }
        
        setTopics(data)
      } catch (error) {
        console.error('Error loading hot topics:', error)
        // Fallback to mock data is handled in fetchHotTopics
        setTopics([])
      } finally {
        setLoading(false)
      }
    }
    
    loadTopics()
    
    // Refresh hot topics every 5 minutes to get latest market data
    const refreshInterval = setInterval(() => {
      loadTopics()
    }, 5 * 60 * 1000) // 5 minutes
    
    return () => {
      clearInterval(refreshInterval)
    }
  }, [])

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  // Check if any topic is using mock data
  const hasMockData = topics.some(t => t.dataSource === 'mock')

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 md:p-6 mb-6">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">今日指标</h2>
        {hasMockData && (
          <span className="text-xs text-yellow-600 px-2 py-1 bg-yellow-50 rounded" title="部分数据为模拟数据">
            Mock
          </span>
        )}
      </div>
      
      {/* Desktop: 5 columns grid */}
      <div className="hidden md:grid md:grid-cols-5 gap-3">
        {topics.map((topic) => (
          <HotTopicCard key={topic.id} topic={topic} />
        ))}
      </div>
      
      {/* Mobile: Horizontal scroll */}
      <div className="md:hidden flex gap-3 overflow-x-auto scrollbar-hide pb-2">
        {topics.map((topic) => (
          <div key={topic.id} className="flex-shrink-0 w-32">
            <HotTopicCard topic={topic} />
          </div>
        ))}
      </div>
    </div>
  )
}

