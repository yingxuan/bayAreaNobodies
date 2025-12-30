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

  // Generate actionable overview line with emotion and action hint
  const generateOverviewLine = (): { text: string; icon: string } => {
    const dayGain = portfolioData?.day_gain || 0
    const dayGainPercent = portfolioData?.day_gain_percent || 0
    const validRisks = riskItems.filter(r => r.title && r.title.length > 0)
    const riskCount = validRisks.length
    
    // Determine financial status
    let financialStatus = ''
    let financialIcon = ''
    if (dayGain > 0) {
      financialStatus = '资产上涨'
      financialIcon = '📈'
    } else if (dayGain < 0) {
      financialStatus = '资产回调'
      financialIcon = '📉'
    } else {
      financialStatus = '资产持平'
      financialIcon = '➡️'
    }
    
    // Generate actionable message
    if (riskCount > 0) {
      // Has actionable items
      if (dayGain < 0) {
        return {
          text: `今天${financialStatus}，但有 ${riskCount} 件事需要你今天处理`,
          icon: financialIcon
        }
      } else if (riskCount >= 2) {
        return {
          text: `今天有 ${riskCount} 个和钱相关的事项，建议查看`,
          icon: '⚠️'
        }
      } else {
        return {
          text: `今天有 1 件事需要处理，建议查看`,
          icon: '✅'
        }
      }
    } else {
      // No actionable items
      if (dayGain < 0) {
        return {
          text: `今天${financialStatus}，暂无紧急事项`,
          icon: financialIcon
        }
      } else {
        return {
          text: `今天一切正常，暂无重要事项`,
          icon: '✅'
        }
      }
    }
  }

  const handleOverviewClick = () => {
    // Scroll to "今天必须做的 3 件事" section
    const element = document.getElementById('today-must-do')
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
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
      
      {/* Overview Line - Actionable with click */}
      {(() => {
        const overview = generateOverviewLine()
        return (
          <div 
            onClick={overview.text.includes('需要') || overview.text.includes('建议') ? handleOverviewClick : undefined}
            className={`bg-white rounded-xl shadow-sm p-4 ${
              overview.text.includes('需要') || overview.text.includes('建议') 
                ? 'cursor-pointer hover:shadow-md transition-all hover:border-blue-300 border border-transparent' 
                : ''
            }`}
          >
            <div className="text-sm text-gray-700 flex items-center gap-2">
              <span className="text-base">{overview.icon}</span>
              <span>{overview.text}</span>
              {(overview.text.includes('需要') || overview.text.includes('建议')) && (
                <span className="text-xs text-blue-600 ml-auto">点击查看 →</span>
              )}
            </div>
          </div>
        )
      })()}
    </div>
  )
}

