/**
 * Market Analysis Section - Conditionally renders MarketAnalysisCard
 * Only renders if there's data, otherwise returns null
 */
'use client'

import { MarketAnalysisCard } from './MarketAnalysisCard'

export function MarketAnalysisSection() {
  // MarketAnalysisCard handles its own conditional rendering
  return <MarketAnalysisCard />
}

