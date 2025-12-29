/**
 * Financial Status Card - Layer 2: Decision (Core)
 * Must show: Total Assets + Today's Gain/Loss + Conclusion
 * This is the ONLY place on homepage to show asset numbers
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { fetchHotTopics, HotTopic } from '../lib/hotTopics'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Generate financial conclusion (no repetition of numbers)
 */
function generateFinancialConclusion(
  portfolioData: any,
  marketTopic: HotTopic | undefined
): string {
  if (!portfolioData) {
    return '数据加载中...'
  }

  const dayGainPercent = portfolioData.day_gain_percent || 0
  const absPercent = Math.abs(dayGainPercent)
  
  const conclusionParts: string[] = []
  
  // Market trend analysis
  if (marketTopic && marketTopic.changePercent) {
    const marketChg = parseFloat(marketTopic.changePercent.replace('%', '').replace('+', ''))
    if (Math.abs(marketChg) > 0.5) {
      if (marketChg > 0 && dayGainPercent > 0) {
        conclusionParts.push('科技股跟随大盘上涨')
      } else if (marketChg < 0 && dayGainPercent < 0) {
        conclusionParts.push('科技股回调，整体市场偏弱')
      } else if (marketChg > 0 && dayGainPercent < 0) {
        conclusionParts.push('科技股逆市下跌')
      } else {
        conclusionParts.push('科技股逆市上涨')
      }
    } else {
      if (absPercent > 1) {
        conclusionParts.push(dayGainPercent > 0 ? '科技股表现强势' : '科技股回调明显')
      } else {
        conclusionParts.push('市场整体平稳')
      }
    }
  } else {
    if (absPercent > 1) {
      conclusionParts.push(dayGainPercent > 0 ? '资产表现良好' : '资产出现回调')
    } else {
      conclusionParts.push('资产基本持平')
    }
  }
  
  return conclusionParts.join('，')
}

export function FinancialStatusCard() {
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [hotTopics, setHotTopics] = useState<HotTopic[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [portfolioRes, topics] = await Promise.all([
        fetch(`${API_URL}/portfolio/db-summary`).catch(() => null),
        fetchHotTopics().catch(() => [])
      ])

      if (portfolioRes?.ok) {
        const data = await portfolioRes.json()
        setPortfolioData(data)
      }
      setHotTopics(topics)
    } catch (error) {
      console.error('Error fetching financial data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 border-2 border-blue-200">
        <div className="text-center py-8 text-gray-500">加载中...</div>
      </div>
    )
  }

  const totalValue = portfolioData?.total_value || 0
  const dayGain = portfolioData?.day_gain || 0
  const dayGainPercent = portfolioData?.day_gain_percent || 0
  
  const marketTopic = hotTopics.find(t => t.id === 'market')
  const financialConclusion = generateFinancialConclusion(portfolioData, marketTopic)

  // Format gain/loss
  const absDayGain = Math.abs(dayGain)
  const absDayGainPercent = Math.abs(dayGainPercent)
  
  let gainSign = ''
  if (dayGain > 0) {
    gainSign = '+'
  } else if (dayGain < 0) {
    gainSign = '-'
  }
  
  let percentSign = ''
  if (dayGainPercent > 0) {
    percentSign = '+'
  } else if (dayGainPercent < 0) {
    percentSign = '-'
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border-2 border-blue-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">💰 财务状态</h2>
        <Link href="/wealth" className="text-sm text-blue-600 hover:text-blue-700">
          查看详情 →
        </Link>
      </div>

      {/* Total Assets */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-1">总资产</div>
        <div className="text-3xl font-bold text-gray-900">
          ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
        </div>
      </div>

      {/* Today's Gain/Loss */}
      <div className="mb-4">
        <div className="text-sm text-gray-600 mb-1">今日涨跌</div>
        {absDayGain < 0.01 && absDayGainPercent < 0.01 ? (
          <div className="text-2xl font-bold text-gray-700">
            $0（0.00%）
          </div>
        ) : (
          <div className={`text-2xl font-bold ${dayGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {gainSign}${absDayGain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}（{percentSign}{absDayGainPercent.toFixed(2)}%）
          </div>
        )}
      </div>

      {/* Conclusion (no repetition of numbers) */}
      <div className="pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-700">
          {financialConclusion}
        </div>
      </div>
    </div>
  )
}

