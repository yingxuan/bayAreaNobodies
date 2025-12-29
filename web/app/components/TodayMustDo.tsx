/**
 * Today Must Do - Layer 2: Decision (Critical)
 * Shows 3 actionable items with checklist style
 * Data source: /risk/today-actions
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type ActionItem = {
  title: string
  why: string
  action: string
  deadline?: string
  severity: 'high' | 'medium' | 'low'
}

type TodayActionsData = {
  items: ActionItem[]
  updatedAt: string
  dataSource: 'gemini' | 'cache' | 'mock'
}

function getSeverityIcon(severity: string): string {
  if (severity === 'high') return '🔴'
  if (severity === 'medium') return '🟡'
  return '🟢'
}

export function TodayMustDo() {
  const [data, setData] = useState<TodayActionsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchActions()
  }, [])

  const fetchActions = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/risk/today-actions?city=cupertino`, {
        cache: 'no-store'
      })
      
      if (res.ok) {
        const result = await res.json()
        setData({
          items: result.items || [],
          updatedAt: result.updatedAt || new Date().toISOString(),
          dataSource: result.dataSource || 'mock'
        })
      }
    } catch (error) {
      console.error('Error fetching today actions:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 border-2 border-orange-200">
        <h2 className="text-xl font-bold text-gray-900 mb-4">✅ 今天必须做的 3 件事</h2>
        <div className="text-sm text-gray-500">加载中...</div>
      </div>
    )
  }

  const items = (data?.items || []).slice(0, 3)
  
  // Fallback mock if empty
  const displayItems = items.length > 0 ? items : [
    {
      title: '检查 401(k) rollover 截止时间',
      why: '避免错过 60 天窗口',
      action: '确认旧账户 rollover 流程',
      deadline: '60 天内',
      severity: 'high' as const
    }
  ]

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border-2 border-orange-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">✅ 今天必须做的 3 件事</h2>
        <Link href="/risk" className="text-sm text-blue-600 hover:text-blue-700">
          查看详情 →
        </Link>
      </div>

      <div className="space-y-3">
        {displayItems.map((item, idx) => (
          <div key={idx} className="flex items-start gap-3">
            <input
              type="checkbox"
              disabled
              className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm">{getSeverityIcon(item.severity)}</span>
                <span className="font-semibold text-gray-900 text-sm line-clamp-1">
                  {item.title}
                </span>
              </div>
              {item.deadline && (
                <div className="text-xs text-gray-500">
                  截止：{item.deadline}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

