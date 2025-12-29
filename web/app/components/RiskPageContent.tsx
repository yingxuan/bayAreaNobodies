'use client'

import { useState, useEffect } from 'react'
import { getRiskItems, getValidRisks, RiskItem } from '../lib/risk'

function formatRelativeTime(isoString: string): string {
  const now = new Date()
  const updated = new Date(isoString)
  const diffMs = now.getTime() - updated.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) {
    return '刚刚'
  } else if (diffMins < 60) {
    return `${diffMins} 分钟前`
  } else {
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) {
      return `${diffHours} 小时前`
    } else {
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays} 天前`
    }
  }
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'high':
      return 'border-red-300 bg-red-50'
    case 'med':
      return 'border-yellow-300 bg-yellow-50'
    case 'low':
      return 'border-blue-300 bg-blue-50'
    default:
      return 'border-gray-300 bg-gray-50'
  }
}

function getSeverityIcon(severity: string): string {
  switch (severity) {
    case 'high':
      return '🔴'
    case 'med':
      return '🟡'
    case 'low':
      return '🟢'
    default:
      return '⚪'
  }
}

export function RiskPageContent() {
  const [risks, setRisks] = useState<RiskItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadRisks()
  }, [])

  const loadRisks = async () => {
    setLoading(true)
    try {
      const allRisks = await getRiskItems('cupertino')
      const validRisks = getValidRisks(allRisks)
      setRisks(validRisks.slice(0, 3)) // Max 3 items
    } catch (error) {
      console.error('Error loading risks:', error)
      setRisks([]) // Never throw, show empty state
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  if (risks.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">✅</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">今日无重要提醒</h2>
        <p className="text-sm text-gray-500">
          当前没有需要特别关注的风险提醒
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {risks.map((risk) => (
        <div
          key={risk.id}
          className={`border-l-4 rounded-lg p-5 ${getSeverityColor(risk.severity)}`}
        >
          {/* Title */}
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <span>{getSeverityIcon(risk.severity)}</span>
              {risk.title}
            </h3>
            {risk.dataSource === 'mock' && (
              <span className="text-xs text-yellow-600 px-2 py-1 bg-yellow-100 rounded" title="模拟数据">
                Mock
              </span>
            )}
            {risk.dataSource === 'stale' && (
              <span className="text-xs text-gray-600 px-2 py-1 bg-gray-100 rounded" title="数据可能已过期">
                Stale
              </span>
            )}
          </div>

          {/* Why */}
          {risk.why && (
            <div className="mb-2">
              <span className="text-sm font-medium text-gray-700">背景：</span>
              <span className="text-sm text-gray-600 ml-2">{risk.why}</span>
            </div>
          )}

          {/* Who */}
          <div className="mb-2">
            <span className="text-sm font-medium text-gray-700">谁需要注意：</span>
            <span className="text-sm text-gray-600 ml-2">{risk.who}</span>
          </div>

          {/* Action */}
          <div className="mb-3">
            <span className="text-sm font-medium text-gray-700">建议行动：</span>
            <span className="text-sm text-gray-600 ml-2">{risk.action}</span>
          </div>

          {/* Deadline */}
          {risk.deadline && (
            <div className="mb-3">
              <span className="text-sm font-medium text-gray-700">截止日期：</span>
              <span className="text-sm text-red-600 font-semibold ml-2">{risk.deadline}</span>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-2">
              <span>更新于 {formatRelativeTime(risk.updatedAt)}</span>
              {risk.category && (
                <span className="px-2 py-0.5 bg-gray-100 rounded">{risk.category}</span>
              )}
            </div>
            {risk.source && (
              <span>来源：{risk.source}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

