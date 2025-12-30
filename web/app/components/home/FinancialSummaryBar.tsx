/**
 * Financial Summary Bar - Full width horizontal bar
 * Highest priority: Total assets, today's gain/loss, top movers
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

export function FinancialSummaryBar() {
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
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-3 py-2.5 h-14 flex items-center">
        <div className="flex items-center gap-6 w-full">
          <div className="w-32 h-5 bg-gray-100 rounded animate-pulse" />
          <div className="w-24 h-5 bg-gray-100 rounded animate-pulse" />
          <div className="w-40 h-5 bg-gray-100 rounded animate-pulse" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-3 py-2.5 h-14 flex items-center">
      <div className="flex items-center justify-between w-full gap-4 overflow-hidden">
        {/* Left: Financial Summary - Horizontal, no wrap */}
        <div className="flex items-center gap-6 flex-1 min-w-0 overflow-x-auto scrollbar-hide">
          {/* Total Assets */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs text-gray-600 whitespace-nowrap">总资产</span>
            <span className="text-lg font-bold text-gray-900 whitespace-nowrap">
              ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </span>
          </div>

          {/* Today's Gain/Loss */}
          {absDayGain < 0.01 && absDayGainPercent < 0.01 ? (
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-xs text-gray-600 whitespace-nowrap">今日涨跌</span>
              <span className="text-base font-bold text-gray-700 whitespace-nowrap">$0（0.00%）</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-xs text-gray-600 whitespace-nowrap">今日涨跌</span>
              <span className={`text-base font-bold whitespace-nowrap ${dayGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {gainSign}${absDayGain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}（{percentSign}{absDayGainPercent.toFixed(2)}%）
              </span>
            </div>
          )}

          {/* Top Movers */}
          {topMovers.length > 0 && (
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="text-xs text-gray-600 whitespace-nowrap">Top Movers:</span>
              <div className="flex items-center gap-1.5">
                {topMovers.slice(0, 3).map((holding: any, idx: number) => {
                  const dayGain = holding.day_gain || 0
                  const dayGainPercent = holding.day_gain_percent || 0
                  const isPositive = dayGain >= 0
                  const absPercent = Math.abs(dayGainPercent)
                  
                  return (
                    <div
                      key={holding.ticker || idx}
                      className="flex items-center gap-1 text-xs px-1.5 py-0.5 bg-gray-50 rounded-full flex-shrink-0"
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
        </div>

        {/* Right: Action Link */}
        <Link href="/wealth" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap flex-shrink-0">
          查看完整持仓 →
        </Link>
      </div>
    </div>
  )
}

