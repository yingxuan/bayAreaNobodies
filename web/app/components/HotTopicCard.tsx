'use client'

import Link from 'next/link'
import { HotTopic } from '../lib/hotTopics'

interface HotTopicCardProps {
  topic: HotTopic
}

export function HotTopicCard({ topic }: HotTopicCardProps) {
  const trendColor = topic.trend === 'up' 
    ? 'text-green-600' 
    : topic.trend === 'down' 
    ? 'text-red-600' 
    : 'text-gray-600'
  
  const trendIcon = topic.trend === 'up' 
    ? '↑' 
    : topic.trend === 'down' 
    ? '↓' 
    : ''

  return (
    <Link
      href={topic.href}
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md hover:border-blue-300 transition-all group"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{topic.icon}</span>
          <span className="text-sm font-medium text-gray-600">{topic.label}</span>
        </div>
        {topic.dataSource === 'mock' && (
          <span className="text-xs text-gray-400">Mock</span>
        )}
      </div>
      
      <div className="space-y-1">
        <div className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors">
          {topic.value}
        </div>
        
        {topic.change && topic.changePercent && (
          <div className={`text-sm font-medium ${trendColor} flex items-center gap-1`}>
            <span>{trendIcon}</span>
            <span>{topic.change}</span>
            <span>({topic.changePercent})</span>
          </div>
        )}
      </div>
    </Link>
  )
}

