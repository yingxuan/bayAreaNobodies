/**
 * Today Alert Bar - Top horizontal alert bar
 * Shows max 3 items: icon + title + deadline + detail link
 * Compressed to 1-2 lines
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type ActionItem = {
  title: string
  deadline?: string
  severity: 'high' | 'medium' | 'low'
}

function getSeverityIcon(severity: string): string {
  if (severity === 'high') return '🔴'
  if (severity === 'medium') return '🟡'
  return '🟢'
}

export function TodayAlertBar() {
  const [items, setItems] = useState<ActionItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchActions()
  }, [])

  const fetchActions = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/risk/today-actions?city=cupertino`).catch(() => null)
      
      if (res?.ok) {
        const result = await res.json()
        const actionItems = (result.items || []).slice(0, 3).map((item: any) => ({
          title: item.title,
          deadline: item.deadline,
          severity: item.severity || 'medium'
        }))
        setItems(actionItems)
      }
    } catch (error) {
      console.error('Error fetching today actions:', error)
    } finally {
      setLoading(false)
    }
  }

  // Fallback mock if empty
  const displayItems = items.length > 0 ? items : [
    {
      title: '检查 401(k) rollover 截止时间',
      deadline: '60 天内',
      severity: 'high' as const
    }
  ]

  if (loading) {
    return (
      <div className="bg-orange-50 border-l-4 border-orange-400 p-3">
        <div className="text-sm text-gray-500">加载中...</div>
      </div>
    )
  }

  if (displayItems.length === 0) {
    return null
  }

  return (
    <div className="bg-orange-50 border-l-4 border-orange-400 px-3 py-2">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <span className="text-orange-700 font-medium">⚠️ 今天必须做：</span>
        {displayItems.map((item, idx) => (
          <span key={idx} className="flex items-center gap-1.5">
            <span className="text-gray-900">• {item.title}</span>
            {item.deadline && (
              <span className="text-xs text-orange-600">({item.deadline})</span>
            )}
          </span>
        ))}
        <Link href="/risk" className="text-xs text-blue-600 hover:text-blue-700 ml-auto">
          详情 →
        </Link>
      </div>
    </div>
  )
}

