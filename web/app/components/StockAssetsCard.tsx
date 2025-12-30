/**
 * Stock Assets Card - (2) 股票资产
 * Shows: Total Assets + Today's Gain/Loss + Top Movers
 * This is the ONLY place on homepage to show personal asset numbers
 */
'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function StockAssetsCard() {
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const portfolioRes = await fetch(`${API_URL}/portfolio/db-summary`).catch(() => null)

      if (portfolioRes?.ok) {
        const data = await portfolioRes.json()
        setPortfolioData(data)
      }
    } catch (error) {
      console.error('Error fetching portfolio data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Get Top 5 Movers (by absolute day_gain amount)
  const getTopMovers = () => {
    if (!portfolioData?.holdings || !Array.isArray(portfolioData.holdings)) {
      return []
    }
    
    const holdings = portfolioData.holdings.filter((h: any) => 
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

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <div className="text-center py-8 text-gray-500">加载中...</div>
      </div>
    )
  }

  const totalValue = portfolioData?.total_value || 0
  const dayGain = portfolioData?.day_gain || 0
  const dayGainPercent = portfolioData?.day_gain_percent || 0

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

  const topMovers = getTopMovers()

  return (
    <div className="h-full">

      {/* Total Assets + Today's Gain/Loss (compact) */}
      <div className="mb-3">
        <div className="text-2xl font-bold text-gray-900 mb-1">
          ${totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
        </div>
        {absDayGain < 0.01 && absDayGainPercent < 0.01 ? (
          <div className="text-lg font-bold text-gray-700">
            $0（0.00%）
          </div>
        ) : (
          <div className={`text-lg font-bold ${dayGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {gainSign}${absDayGain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}（{percentSign}{absDayGainPercent.toFixed(2)}%）
          </div>
        )}
      </div>

      {/* Top Movers - Single row horizontal */}
      {topMovers.length > 0 && (
        <div className="pt-2 border-t border-gray-100">
          <div className="flex items-center gap-3 flex-wrap">
            {topMovers.map((holding: any, idx: number) => {
              const dayGain = holding.day_gain || 0
              const dayGainPercent = holding.day_gain_percent || 0
              const isPositive = dayGain >= 0
              const absGain = Math.abs(dayGain)
              const absPercent = Math.abs(dayGainPercent)
              
              return (
                <div
                  key={holding.ticker || idx}
                  className="flex items-center gap-1.5 text-xs"
                >
                  <span className="font-medium text-gray-900">{holding.ticker}</span>
                  <span className={`font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                    {isPositive ? '+' : '-'}{absPercent.toFixed(1)}%
                  </span>
                  <span className={`text-gray-500 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                    ({isPositive ? '+' : '-'}${absGain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })})
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

