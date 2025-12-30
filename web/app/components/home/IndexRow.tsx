/**
 * Index Row - Compact market indicators
 * Shows: SPY, Gold, BTC, California Jumbo Loan Rate, Powerball Jackpot
 */
'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type MarketSnapshot = {
  sp500?: {
    price: number
    chgPct24h?: number
    stale?: boolean
  }
  btc?: {
    price: number
    chgPct24h?: number
    stale?: boolean
  }
  gold?: {
    price: number
    chgPct24h?: number
    stale?: boolean
  }
  mortgage30y?: {
    rate: number
    weekDate?: string
    stale?: boolean
  }
  lottery?: {
    game: string
    jackpot: number
    drawDate?: string
    stale?: boolean
  }
}

export function IndexRow() {
  const [marketData, setMarketData] = useState<MarketSnapshot | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMarketData()
    // Refresh every 5 minutes
    const interval = setInterval(fetchMarketData, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const fetchMarketData = async () => {
    try {
      const res = await fetch(`${API_URL}/market/snapshot`).catch(() => null)
      if (res?.ok) {
        const data = await res.json()
        setMarketData(data)
      }
    } catch (error) {
      console.error('Error fetching market data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 sm:px-4 py-1.5 overflow-x-auto scrollbar-hide border-t border-gray-100">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="w-20 h-5 bg-gray-100 rounded animate-pulse flex-shrink-0" />
        ))}
      </div>
    )
  }

  if (!marketData) {
    return null
  }

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `$${(price / 1000000).toFixed(1)}M`
    } else if (price >= 1000) {
      return `$${(price / 1000).toFixed(0)}K`
    }
    return `$${price.toFixed(0)}`
  }

  const formatChange = (chg?: number) => {
    if (chg === undefined || chg === null) return ''
    const sign = chg >= 0 ? '+' : ''
    return `${sign}${chg.toFixed(2)}%`
  }

  const indicators: Array<{
    label: string
    value: string
    change?: string
    color: string
  }> = []

  // SPY (S&P 500)
  if (marketData.sp500 && marketData.sp500.price > 0) {
    const chg = marketData.sp500.chgPct24h || 0
    indicators.push({
      label: 'SPY',
      value: marketData.sp500.price.toFixed(0),
      change: formatChange(chg),
      color: chg >= 0 ? 'text-green-600' : chg < 0 ? 'text-red-600' : 'text-gray-600'
    })
  }

  // Gold
  if (marketData.gold && marketData.gold.price > 0) {
    const chg = marketData.gold.chgPct24h || 0
    indicators.push({
      label: 'Gold',
      value: `$${marketData.gold.price.toFixed(0)}`,
      change: formatChange(chg),
      color: chg >= 0 ? 'text-green-600' : chg < 0 ? 'text-red-600' : 'text-gray-600'
    })
  }

  // BTC
  if (marketData.btc && marketData.btc.price > 0) {
    const chg = marketData.btc.chgPct24h || 0
    indicators.push({
      label: 'BTC',
      value: formatPrice(marketData.btc.price),
      change: formatChange(chg),
      color: chg >= 0 ? 'text-green-600' : chg < 0 ? 'text-red-600' : 'text-gray-600'
    })
  }

  // California Jumbo Loan Rate
  if (marketData.mortgage30y && marketData.mortgage30y.rate > 0) {
    indicators.push({
      label: 'CA Jumbo 7/1 ARM',
      value: `${marketData.mortgage30y.rate.toFixed(2)}%`,
      change: undefined,
      color: 'text-gray-600'
    })
  }

  // Powerball Jackpot
  if (marketData.lottery && marketData.lottery.jackpot > 0) {
    indicators.push({
      label: 'Powerball',
      value: formatPrice(marketData.lottery.jackpot),
      change: undefined,
      color: 'text-purple-600'
    })
  }

  // Group indicators
  const indexGroup: typeof indicators = []
  const commodityGroup: typeof indicators = []
  const ratesGroup: typeof indicators = []

  indicators.forEach((indicator) => {
    if (indicator.label === 'SPY' || indicator.label === 'QQQ') {
      indexGroup.push(indicator)
    } else if (indicator.label === 'Gold' || indicator.label === 'BTC') {
      commodityGroup.push(indicator)
    } else {
      ratesGroup.push(indicator)
    }
  })

  if (indicators.length === 0) {
    return null
  }

  return (
    <div className="px-3 sm:px-4 py-1.5 border-t border-gray-100">
      {/* Desktop: Groups in one row with separators */}
      <div className="hidden sm:flex items-center gap-2 sm:gap-3 flex-wrap">
        {/* Group A: Indices */}
        {indexGroup.length > 0 && (
          <>
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500 font-medium">指数</span>
              {indexGroup.map((indicator, idx) => (
                <div key={idx} className="flex items-center gap-1 text-xs">
                  <span className="text-gray-600 font-medium whitespace-nowrap">{indicator.label}:</span>
                  <span className="font-semibold text-gray-900 whitespace-nowrap">{indicator.value}</span>
                  {indicator.change && (
                    <span className={`${indicator.color} whitespace-nowrap`}>{indicator.change}</span>
                  )}
                </div>
              ))}
            </div>
            {(commodityGroup.length > 0 || ratesGroup.length > 0) && (
              <span className="text-gray-300">|</span>
            )}
          </>
        )}

        {/* Group B: Commodities */}
        {commodityGroup.length > 0 && (
          <>
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-gray-500 font-medium">黄金&加密</span>
              {commodityGroup.map((indicator, idx) => (
                <div key={idx} className="flex items-center gap-1 text-xs">
                  <span className="text-gray-600 font-medium whitespace-nowrap">{indicator.label}:</span>
                  <span className="font-semibold text-gray-900 whitespace-nowrap">{indicator.value}</span>
                  {indicator.change && (
                    <span className={`${indicator.color} whitespace-nowrap`}>{indicator.change}</span>
                  )}
                </div>
              ))}
            </div>
            {ratesGroup.length > 0 && (
              <span className="text-gray-300">|</span>
            )}
          </>
        )}

        {/* Group C: Rates/Other */}
        {ratesGroup.length > 0 && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-gray-500 font-medium">利率&其他</span>
            {ratesGroup.map((indicator, idx) => (
              <div key={idx} className="flex items-center gap-1 text-xs">
                <span className="text-gray-600 font-medium whitespace-nowrap">{indicator.label}:</span>
                <span className="font-semibold text-gray-900 whitespace-nowrap">{indicator.value}</span>
                {indicator.change && (
                  <span className={`${indicator.color} whitespace-nowrap`}>{indicator.change}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Mobile: Horizontal scrollable chips with group separators */}
      <div className="sm:hidden overflow-x-auto scrollbar-hide pb-1">
        <div className="flex items-center gap-2">
          {/* Group A: Indices */}
          {indexGroup.length > 0 && (
            <>
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <span className="text-xs text-gray-500 font-medium px-1">指数</span>
                {indexGroup.map((indicator, idx) => (
                  <div key={idx} className="flex items-center gap-1 text-xs px-1.5 py-0.5 bg-gray-50 rounded-full flex-shrink-0">
                    <span className="text-gray-600 font-medium whitespace-nowrap">{indicator.label}:</span>
                    <span className="font-semibold text-gray-900 whitespace-nowrap">{indicator.value}</span>
                    {indicator.change && (
                      <span className={`${indicator.color} whitespace-nowrap`}>{indicator.change}</span>
                    )}
                  </div>
                ))}
              </div>
              {(commodityGroup.length > 0 || ratesGroup.length > 0) && (
                <span className="text-gray-300 flex-shrink-0">|</span>
              )}
            </>
          )}

          {/* Group B: Commodities */}
          {commodityGroup.length > 0 && (
            <>
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <span className="text-xs text-gray-500 font-medium px-1">黄金&加密</span>
                {commodityGroup.map((indicator, idx) => (
                  <div key={idx} className="flex items-center gap-1 text-xs px-1.5 py-0.5 bg-gray-50 rounded-full flex-shrink-0">
                    <span className="text-gray-600 font-medium whitespace-nowrap">{indicator.label}:</span>
                    <span className="font-semibold text-gray-900 whitespace-nowrap">{indicator.value}</span>
                    {indicator.change && (
                      <span className={`${indicator.color} whitespace-nowrap`}>{indicator.change}</span>
                    )}
                  </div>
                ))}
              </div>
              {ratesGroup.length > 0 && (
                <span className="text-gray-300 flex-shrink-0">|</span>
              )}
            </>
          )}

          {/* Group C: Rates/Other */}
          {ratesGroup.length > 0 && (
            <div className="flex items-center gap-1.5 flex-shrink-0">
              <span className="text-xs text-gray-500 font-medium px-1">利率&其他</span>
              {ratesGroup.map((indicator, idx) => (
                <div key={idx} className="flex items-center gap-1 text-xs px-1.5 py-0.5 bg-gray-50 rounded-full flex-shrink-0">
                  <span className="text-gray-600 font-medium whitespace-nowrap">{indicator.label}:</span>
                  <span className="font-semibold text-gray-900 whitespace-nowrap">{indicator.value}</span>
                  {indicator.change && (
                    <span className={`${indicator.color} whitespace-nowrap`}>{indicator.change}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

