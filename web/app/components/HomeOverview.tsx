/**
 * Home Overview - Layer 1: State (10 seconds scan)
 * Shows: TodayCommandBar + Overview Line
 */
'use client'

import { useState, useEffect } from 'react'
import { TodayCommandBar } from './TodayCommandBar'
import { fetchHotTopics, HotTopic } from '../lib/hotTopics'
import { getRiskItems, RiskItem } from '../lib/risk'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function HomeOverview() {
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [riskItems, setRiskItems] = useState<RiskItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOverview()
  }, [])

  const fetchOverview = async () => {
    setLoading(true)
    try {
      const [portfolioRes, riskData] = await Promise.all([
        fetch(`${API_URL}/portfolio/db-summary`).catch(() => null),
        getRiskItems('cupertino').catch(() => [])
      ])

      if (portfolioRes?.ok) {
        const data = await portfolioRes.json()
        setPortfolioData(data)
      }
      setRiskItems(riskData)
    } catch (error) {
      console.error('Error fetching overview:', error)
    } finally {
      setLoading(false)
    }
  }

  // Generate overview line
  const generateOverviewLine = (): string => {
    const parts: string[] = []
    
    if (portfolioData) {
      const dayGain = portfolioData.day_gain || 0
      const dayGainPercent = portfolioData.day_gain_percent || 0
      
      if (dayGain > 0) {
        parts.push('资产上涨')
      } else if (dayGain < 0) {
        parts.push('资产下跌')
      } else {
        parts.push('资产持平')
      }
    }
    
    const validRisks = riskItems.filter(r => r.title && r.title.length > 0)
    if (validRisks.length > 0) {
      parts.push(`有 ${validRisks.length} 件需要注意的事`)
    } else {
      parts.push('暂无重要事项')
    }
    
    return parts.join(' ｜ ')
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <TodayCommandBar />
        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="text-sm text-gray-500">今日概览：加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <TodayCommandBar />
      
      {/* Overview Line */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="text-sm text-gray-700">
          <span className="font-medium">今日概览：</span>
          {generateOverviewLine()}
        </div>
      </div>
    </div>
  )
}

