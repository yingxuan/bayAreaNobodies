/**
 * Wealth Summary Header - Compact header for Section 1
 * Combines portfolio summary + market indicators + breaking news
 * Layout: 2-3 rows (KPI row, Market groups row, optional Breaking News)
 */
'use client'

import { FinancialSummaryBar } from './FinancialSummaryBar'
import { IndexRow } from './IndexRow'
import { BreakingNewsTicker } from './BreakingNewsTicker'

export function WealthSummaryHeader() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Row 1: KPI Row (股票市值, 今日涨跌, 总浮盈, YTD%, Top Movers) */}
      <FinancialSummaryBar />
      
      {/* Row 2: Market Groups Row (指数 / 黄金&加密 / 利率&其他) */}
      <IndexRow />
      
      {/* Row 3: Breaking News Ticker (only if data exists) */}
      <BreakingNewsTicker />
    </div>
  )
}

