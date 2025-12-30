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
  total_cost: number
  total_pnl: number
  total_pnl_percent: number
  day_gain: number
  day_gain_percent: number
  ytd_percent?: number
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
  const totalCost = data?.total_cost || 0
  const totalPnl = data?.total_pnl || 0
  const totalPnlPercent = data?.total_pnl_percent || 0
  const dayGain = data?.day_gain || 0
  const dayGainPercent = data?.day_gain_percent || 0
  const topMovers = getTopMovers()

  // Format gain/loss
  const absDayGain = Math.abs(dayGain)
  const absDayGainPercent = Math.abs(dayGainPercent)
  const absTotalPnl = Math.abs(totalPnl)
  const absTotalPnlPercent = Math.abs(totalPnlPercent)
  
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

  // YTD calculation: Use ytd_percent from API if available, otherwise use total_pnl_percent as approximation
  // Note: total_pnl_percent is return on cost basis, not true YTD%
  // True YTD% = (current_value - year_start_value) / year_start_value * 100
  // We need year_start_value to calculate accurate YTD%
  const ytdPercent = data?.ytd_percent !== undefined ? data.ytd_percent : totalPnlPercent
  const hasYtdData = totalCost > 0 // If we have cost basis, we can calculate

  if (loading) {
    return (
      <div className="px-3 sm:px-4 py-2.5 space-y-2">
        <div className="flex items-center gap-4 w-full">
          <div className="w-32 h-5 bg-gray-100 rounded animate-pulse" />
          <div className="w-24 h-5 bg-gray-100 rounded animate-pulse" />
        </div>
        <div className="w-40 h-4 bg-gray-100 rounded animate-pulse" />
      </div>
    )
  }

  // Calculate remaining movers count
  const visibleMovers = topMovers.slice(0, 2)
  const remainingCount = topMovers.length > 2 ? topMovers.length - 2 : 0

  // Format total P&L
  const totalPnlSign = totalPnl >= 0 ? '+' : '-'
  const totalPnlPercentSign = totalPnlPercent >= 0 ? '+' : '-'

  return (
    <div className="px-3 sm:px-4 py-2.5 space-y-2">
      {/* Row 1: KPI Row - Desktop: single row, Mobile: two rows */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 w-full min-w-0">
        {/* Desktop: All KPIs in one row */}
        <div className="hidden sm:flex items-center gap-2 sm:gap-3 flex-1 min-w-0">
          {/* 股票市值 */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <span className="text-xs text-gray-600 whitespace-nowrap">股票市值</span>
            <span className="text-base sm:text-lg font-bold text-gray-900 whitespace-nowrap">
              ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </span>
          </div>

          {/* 今日涨跌 */}
          {absDayGain < 0.01 && absDayGainPercent < 0.01 ? (
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs text-gray-600 whitespace-nowrap">今日涨跌</span>
              <span className="text-xs sm:text-sm font-bold text-gray-700 whitespace-nowrap">$0（0.00%）</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs text-gray-600 whitespace-nowrap">今日涨跌</span>
              <span className={`text-xs sm:text-sm font-bold whitespace-nowrap ${dayGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {gainSign}${absDayGain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}（{percentSign}{absDayGainPercent.toFixed(2)}%）
              </span>
            </div>
          )}

          {/* 总浮盈 */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <span className="text-xs text-gray-600 whitespace-nowrap">总浮盈</span>
            <span className={`text-xs sm:text-sm font-bold whitespace-nowrap ${totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {totalPnlSign}${absTotalPnl.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </span>
          </div>

          {/* YTD% */}
          {hasYtdData ? (
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs text-gray-600 whitespace-nowrap">YTD%</span>
              <span className={`text-xs sm:text-sm font-bold whitespace-nowrap ${ytdPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {ytdPercent >= 0 ? '+' : ''}{Math.abs(ytdPercent).toFixed(2)}%
              </span>
            </div>
          ) : null}

          {/* Top Movers - Max 2 visible, then +N */}
          {topMovers.length > 0 && (
            <div className="flex items-center gap-1.5 flex-1 min-w-0">
              <span className="text-xs text-gray-600 whitespace-nowrap flex-shrink-0">Top:</span>
              <div className="flex items-center gap-1 flex-1 min-w-0 overflow-hidden">
                {visibleMovers.map((holding: any, idx: number) => {
                  const dayGain = holding.day_gain || 0
                  const dayGainPercent = holding.day_gain_percent || 0
                  const isPositive = dayGain >= 0
                  const absPercent = Math.abs(dayGainPercent)
                  
                  return (
                    <div
                      key={holding.ticker || idx}
                      className="flex items-center gap-0.5 text-xs px-1.5 py-0.5 bg-gray-50 rounded-full flex-shrink-0"
                      title={`${holding.ticker}: ${isPositive ? '+' : '-'}$${Math.abs(dayGain).toFixed(2)}`}
                    >
                      <span className="font-medium text-gray-900">{holding.ticker}</span>
                      <span className={`font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {isPositive ? '+' : '-'}{absPercent.toFixed(1)}%
                      </span>
                    </div>
                  )
                })}
                {remainingCount > 0 && (
                  <span className="text-xs text-gray-500 font-medium flex-shrink-0">+{remainingCount}</span>
                )}
              </div>
            </div>
          )}

          {/* Action Link */}
          <Link href="/wealth" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap flex-shrink-0">
            更多 →
          </Link>
        </div>

        {/* Mobile: Two rows */}
        <div className="flex sm:hidden flex-col gap-2 w-full">
          {/* Row 1: 股票市值 + 今日涨跌 */}
          <div className="flex items-center gap-2 sm:gap-3 w-full">
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs text-gray-600 whitespace-nowrap">股票市值</span>
              <span className="text-base font-bold text-gray-900 whitespace-nowrap">
                ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </span>
            </div>
            {absDayGain < 0.01 && absDayGainPercent < 0.01 ? (
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <span className="text-xs text-gray-600 whitespace-nowrap">今日涨跌</span>
                <span className="text-xs font-bold text-gray-700 whitespace-nowrap">$0（0.00%）</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <span className="text-xs text-gray-600 whitespace-nowrap">今日涨跌</span>
                <span className={`text-xs font-bold whitespace-nowrap ${dayGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {gainSign}${absDayGain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}（{percentSign}{absDayGainPercent.toFixed(2)}%）
                </span>
              </div>
            )}
            <Link href="/wealth" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap flex-shrink-0 ml-auto">
              更多 →
            </Link>
          </div>

          {/* Row 2: 总浮盈 + YTD% + Top Movers */}
          <div className="flex items-center gap-2 flex-1 min-w-0 overflow-x-auto scrollbar-hide">
            {/* 总浮盈 */}
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs text-gray-600 whitespace-nowrap">总浮盈</span>
              <span className={`text-xs font-bold whitespace-nowrap ${totalPnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {totalPnlSign}${absTotalPnl.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
              </span>
            </div>

            {/* YTD% */}
            {hasYtdData && (
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <span className="text-xs text-gray-600 whitespace-nowrap">YTD%</span>
                <span className={`text-xs font-bold whitespace-nowrap ${ytdPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {ytdPercent >= 0 ? '+' : ''}{Math.abs(ytdPercent).toFixed(2)}%
                </span>
              </div>
            )}

            {/* Top Movers - Truncated on mobile */}
            {topMovers.length > 0 && (
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <span className="text-xs text-gray-600 whitespace-nowrap">Top:</span>
                <div className="flex items-center gap-1">
                  {visibleMovers.map((holding: any, idx: number) => {
                    const dayGain = holding.day_gain || 0
                    const dayGainPercent = holding.day_gain_percent || 0
                    const isPositive = dayGain >= 0
                    const absPercent = Math.abs(dayGainPercent)
                    
                    return (
                      <div
                        key={holding.ticker || idx}
                        className="flex items-center gap-0.5 text-xs px-1.5 py-0.5 bg-gray-50 rounded-full flex-shrink-0"
                        title={`${holding.ticker}: ${isPositive ? '+' : '-'}$${Math.abs(dayGain).toFixed(2)}`}
                      >
                        <span className="font-medium text-gray-900">{holding.ticker}</span>
                        <span className={`font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                          {isPositive ? '+' : '-'}{absPercent.toFixed(1)}%
                        </span>
                      </div>
                    )
                  })}
                  {remainingCount > 0 && (
                    <span className="text-xs text-gray-500 font-medium flex-shrink-0">+{remainingCount}</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

