'use client'

import Link from 'next/link'
import { RiskItem, getValidRisks } from '../lib/risk'

interface RiskStatusLightProps {
  risks: RiskItem[]
}

export function RiskStatusLight({ risks }: RiskStatusLightProps) {
  const validRisks = getValidRisks(risks)
  const hasRisks = validRisks.length > 0
  const firstRisk = validRisks[0]
  const hasMockOrStale = risks.some(r => r.dataSource === 'mock' || r.dataSource === 'stale')

  // State A: No valid risks (default - low presence)
  if (!hasRisks) {
    return (
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm">
        <div className="flex items-center gap-2 text-gray-600">
          <span>✅</span>
          <span>风险状态：暂无重要提醒</span>
        </div>
        {hasMockOrStale && (
          <span className="text-xs text-gray-500 px-2 py-0.5 bg-gray-100 rounded">
            {risks.some(r => r.dataSource === 'mock') ? 'Mock' : 'Stale'}
          </span>
        )}
      </div>
    )
  }

  // State B: Has valid risks (higher contrast)
  const severityColor = firstRisk.severity === 'high' 
    ? 'border-red-300 bg-red-50' 
    : firstRisk.severity === 'med'
    ? 'border-yellow-300 bg-yellow-50'
    : 'border-blue-300 bg-blue-50'
  
  const severityIcon = firstRisk.severity === 'high' 
    ? '🔴' 
    : firstRisk.severity === 'med'
    ? '🟡'
    : '🟢'

  const titleTruncated = firstRisk.title.length > 40 
    ? firstRisk.title.substring(0, 40) + '...'
    : firstRisk.title

  return (
    <Link
      href="/risk"
      className={`flex items-center justify-between px-4 py-2 border rounded-lg text-sm hover:shadow-sm transition-all ${severityColor}`}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <span>{severityIcon}</span>
        <span className="font-medium text-gray-900">
          有 {validRisks.length} 条需要注意：{titleTruncated}
        </span>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0 ml-2">
        {hasMockOrStale && (
          <span className="text-xs text-gray-600 px-2 py-0.5 bg-white/50 rounded">
            {risks.some(r => r.dataSource === 'mock') ? 'Mock' : 'Stale'}
          </span>
        )}
        <span className="text-blue-600 font-medium">查看详情 →</span>
      </div>
    </Link>
  )
}

