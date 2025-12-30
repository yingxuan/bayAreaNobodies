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

  const fetchActions = async (refresh = false) => {
    setLoading(true)
    try {
      const url = refresh 
        ? `${API_URL}/risk/today-actions?city=cupertino&refresh=1`
        : `${API_URL}/risk/today-actions?city=cupertino`
      
      const res = await fetch(url, {
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

  const handleRefresh = () => {
    fetchActions(true)
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
    <div id="today-must-do" className="bg-white rounded-lg shadow-sm p-4 border border-orange-200 h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-bold text-gray-900">✅ 今天提醒</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className="text-xs text-gray-600 hover:text-gray-900 px-1.5 py-0.5 rounded hover:bg-gray-100"
            title="换一批"
          >
            换一批
          </button>
          <Link href="/risk" className="text-xs text-blue-600 hover:text-blue-700">
            详情 →
          </Link>
        </div>
      </div>

      <div className="space-y-2">
        {displayItems.map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <input
              type="checkbox"
              disabled
              className="w-3.5 h-3.5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 flex-shrink-0"
            />
            <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
              <div className="flex items-center gap-1.5 flex-1 min-w-0">
                <span className="text-xs">{getSeverityIcon(item.severity)}</span>
                <span className="font-medium text-gray-900 text-xs line-clamp-1">
                  {item.title}
                </span>
              </div>
              {item.deadline && (
                <span className="text-xs text-orange-600 font-medium flex-shrink-0">
                  {item.deadline}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

