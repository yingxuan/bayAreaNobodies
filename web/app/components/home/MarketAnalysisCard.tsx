/**
 * Market Analysis Card - Compact market summary
 * Shows one-sentence summary OR compact stat list (index, sector, sentiment)
 * Only renders if there's data
 */
'use client'

import { useState, useEffect } from 'react'
import { StandardCard } from './StandardCard'

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
  stale?: boolean
}

export function MarketAnalysisCard() {
  const [marketData, setMarketData] = useState<MarketSnapshot | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMarketData()
  }, [])

  const fetchMarketData = async () => {
    setLoading(true)
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

  // Generate one-sentence market summary
  const generateSummary = (): string => {
    if (!marketData) return ''
    
    const sp500 = marketData.sp500
    const btc = marketData.btc
    const gold = marketData.gold
    
    // Check if we have valid data
    const hasSp500 = sp500 && sp500.price > 0
    const hasBtc = btc && btc.price > 0
    const hasGold = gold && gold.price > 0
    
    if (!hasSp500 && !hasBtc && !hasGold) {
      return ''
    }
    
    // Build summary based on available data
    const parts: string[] = []
    
    if (hasSp500) {
      const chg = sp500.chgPct24h || 0
      if (chg > 0.1) {
        parts.push('美股上涨')
      } else if (chg < -0.1) {
        parts.push('美股下跌')
      } else {
        parts.push('美股平稳')
      }
    }
    
    if (hasBtc) {
      const chg = btc.chgPct24h || 0
      if (chg > 1) {
        parts.push('BTC 上涨')
      } else if (chg < -1) {
        parts.push('BTC 下跌')
      }
    }
    
    if (hasGold) {
      const chg = gold.chgPct24h || 0
      if (chg > 0.5) {
        parts.push('黄金上涨')
      } else if (chg < -0.5) {
        parts.push('黄金下跌')
      }
    }
    
    if (parts.length === 0) {
      return '' // Return empty string, not placeholder
    }
    
    return parts.join('，') + '。'
  }

  // Get compact stats
  const getCompactStats = () => {
    if (!marketData) return null
    
    const sp500 = marketData.sp500
    const btc = marketData.btc
    const gold = marketData.gold
    
    const stats: Array<{ label: string; value: string; trend?: 'up' | 'down' | 'neutral' }> = []
    
    if (sp500 && sp500.price > 0) {
      const chg = sp500.chgPct24h || 0
      stats.push({
        label: 'S&P 500',
        value: sp500.price.toFixed(0),
        trend: chg > 0.1 ? 'up' : chg < -0.1 ? 'down' : 'neutral'
      })
    }
    
    if (btc && btc.price > 0) {
      const chg = btc.chgPct24h || 0
      stats.push({
        label: 'BTC',
        value: `$${(btc.price / 1000).toFixed(0)}K`,
        trend: chg > 1 ? 'up' : chg < -1 ? 'down' : 'neutral'
      })
    }
    
    if (gold && gold.price > 0) {
      const chg = gold.chgPct24h || 0
      stats.push({
        label: 'Gold',
        value: `$${gold.price.toFixed(0)}`,
        trend: chg > 0.5 ? 'up' : chg < -0.5 ? 'down' : 'neutral'
      })
    }
    
    return stats.length > 0 ? stats : null
  }

  // Don't render loading state - wait for data
  if (loading) {
    return null
  }

  // Don't render if no data
  if (!marketData) {
    return null
  }

  const summary = generateSummary()
  const stats = getCompactStats()

  // Don't render if no valid data (empty sections are worse than missing sections)
  if (!summary && !stats) {
    return null
  }

  // Prefer summary, fallback to stats
  const displayContent = summary || (stats && stats.length > 0)

  if (!displayContent) {
    return null
  }

  return (
    <StandardCard title="📈 市场分析" viewMoreHref="/wealth">
      {summary ? (
        // One-sentence summary (preferred)
        <div className="text-sm text-gray-700 leading-relaxed">
          {summary}
        </div>
      ) : stats && stats.length > 0 ? (
        // Compact stat list (fallback)
        <div className="flex flex-wrap items-center gap-3">
          {stats.map((stat, idx) => (
            <div key={idx} className="flex items-center gap-1.5">
              <span className="text-xs text-gray-600">{stat.label}:</span>
              <span className="text-sm font-semibold text-gray-900">{stat.value}</span>
              {stat.trend === 'up' && (
                <span className="text-xs text-green-600">↑</span>
              )}
              {stat.trend === 'down' && (
                <span className="text-xs text-red-600">↓</span>
              )}
            </div>
          ))}
        </div>
      ) : null}
    </StandardCard>
  )
}

