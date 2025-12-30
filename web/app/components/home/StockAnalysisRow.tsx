/**
 * Stock Analysis Row - Conditionally renders Market Analysis + Videos
 * Adjusts layout based on whether Market Analysis has data
 */
'use client'

import { useState, useEffect } from 'react'
import { MarketAnalysisCard } from './MarketAnalysisCard'
import { YouTubeCarousel } from './YouTubeCarousel'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function StockAnalysisRow() {
  const [hasMarketData, setHasMarketData] = useState<boolean | null>(null)

  useEffect(() => {
    checkMarketData()
  }, [])

  const checkMarketData = async () => {
    try {
      const res = await fetch(`${API_URL}/market/snapshot`).catch(() => null)
      if (res?.ok) {
        const data = await res.json()
        // Check if we have valid market data
        const hasSp500 = data.sp500 && data.sp500.price > 0
        const hasBtc = data.btc && data.btc.price > 0
        const hasGold = data.gold && data.gold.price > 0
        setHasMarketData(hasSp500 || hasBtc || hasGold)
      } else {
        setHasMarketData(false)
      }
    } catch (error) {
      setHasMarketData(false)
    }
  }

  // Don't render anything while checking
  if (hasMarketData === null) {
    return (
      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 flex">
          <YouTubeCarousel
            category="stock"
            title="📺 美股分析视频"
            viewMoreHref="/videos/stocks"
            limit={3}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-12 gap-3">
      {/* Left: Market Analysis (only if data available) */}
      {hasMarketData && (
        <div className="col-span-12 lg:col-span-6 flex">
          <MarketAnalysisCard />
        </div>
      )}

      {/* Right: Stock Videos */}
      <div className={`flex ${hasMarketData ? 'col-span-12 lg:col-span-6' : 'col-span-12'}`}>
        <YouTubeCarousel
          category="stock"
          title="📺 美股分析视频"
          viewMoreHref="/videos/stocks"
          limit={3}
        />
      </div>
    </div>
  )
}

