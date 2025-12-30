/**
 * Stock Summary Card - Left side of Stock Row (col-span-7)
 * Displays: Total assets, Today's gain/loss, Top movers, One-line conclusion
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type PortfolioData = {
  total_value: number
  day_gain: number
  day_gain_percent: number
  holdings: Array<{
    ticker: string
    day_gain?: number
    day_gain_percent?: number
  }>
}

export function StockSummaryCard() {
  const [data, setData] = useState<PortfolioData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/portfolio/db-summary`).catch(() => null)
      if (res?.ok) {
        const result = await res.json()
        setData(result)
      }
    } catch (error) {
      console.error('Error fetching portfolio data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Get Top Movers (by absolute day_gain amount)
  const getTopMovers = () => {
    if (!data?.holdings || !Array.isArray(data.holdings)) {
      return []
    }
    
    const holdings = data.holdings.filter((h: any) => 
      h.day_gain !== null && h.day_gain !== undefined && h.ticker
    )
    
    // Sort by absolute day_gain (descending)
    const sorted = [...holdings].sort((a, b) => {
      const absA = Math.abs(a.day_gain || 0)
      const absB = Math.abs(b.day_gain || 0)
      return absB - absA
    })
    
    return sorted.slice(0, 5)
  }

  // Generate one-line Chinese conclusion
  const generateConclusion = (): string => {
    if (!data) return '暂无数据'
    
    const dayGain = data.day_gain || 0
    const dayGainPercent = data.day_gain_percent || 0
    const topMovers = getTopMovers()
    
    // Get top gainers and losers
    const gainers = topMovers.filter((h: any) => (h.day_gain || 0) > 0)
    const losers = topMovers.filter((h: any) => (h.day_gain || 0) < 0)
    
    // Generate conclusion based on market movement
    if (Math.abs(dayGainPercent) < 0.1) {
      return '市场波动较小，整体平稳'
    }
    
    if (dayGainPercent > 0) {
      const topTickers = gainers.slice(0, 2).map((h: any) => h.ticker).join('/')
      return `科技股上涨为主${topTickers ? `，关注 ${topTickers} 波动` : ''}`
    } else {
      const topTickers = losers.slice(0, 2).map((h: any) => h.ticker).join('/')
      return `科技股回调为主${topTickers ? `，关注 ${topTickers} 波动` : ''}`
    }
  }

  const totalValue = data?.total_value || 0
  const dayGain = data?.day_gain || 0
  const dayGainPercent = data?.day_gain_percent || 0
  const topMovers = getTopMovers()

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

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex items-center justify-center">
        <div className="text-sm text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      {/* Header */}
      <div className="mb-3 min-h-[44px] flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900">📈 股票资产</h2>
        <Link href="/wealth" className="text-xs text-blue-600 hover:text-blue-700">
          查看完整持仓 →
        </Link>
      </div>

      {/* Content */}
      <div className="flex-1 space-y-2">
        {/* Total Assets */}
        <div>
          <div className="text-2xl font-bold text-gray-900">
            总资产：${totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </div>
        </div>

        {/* Today's Gain/Loss */}
        {absDayGain < 0.01 && absDayGainPercent < 0.01 ? (
          <div className="text-lg font-bold text-gray-700">
            今日涨跌：$0（0.00%）
          </div>
        ) : (
          <div className={`text-lg font-bold ${dayGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            今日涨跌：{gainSign}${absDayGain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}（{percentSign}{absDayGainPercent.toFixed(2)}%）
          </div>
        )}

        {/* Top Movers - Horizontal pills */}
        {topMovers.length > 0 && (
          <div className="pt-2">
            <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide pb-1">
              <span className="text-xs text-gray-600 flex-shrink-0">Top Movers:</span>
              {topMovers.map((holding: any, idx: number) => {
                const dayGain = holding.day_gain || 0
                const dayGainPercent = holding.day_gain_percent || 0
                const isPositive = dayGain >= 0
                const absPercent = Math.abs(dayGainPercent)
                
                return (
                  <div
                    key={holding.ticker || idx}
                    className="flex items-center gap-1.5 text-xs px-2.5 py-1 bg-gray-50 rounded-full flex-shrink-0"
                    title={`${holding.ticker}: ${isPositive ? '+' : '-'}$${Math.abs(dayGain).toFixed(2)}`}
                  >
                    <span className="font-medium text-gray-900">{holding.ticker}</span>
                    <span className={`font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                      {isPositive ? '+' : '-'}{absPercent.toFixed(1)}%
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* One-line conclusion */}
        <div className="pt-2 border-t border-gray-100">
          <p className="text-sm text-gray-700">{generateConclusion()}</p>
        </div>
      </div>
    </div>
  )
}

