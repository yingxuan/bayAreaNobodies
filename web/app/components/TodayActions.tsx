'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type ActionItem = {
  title: string
  why: string
  action: string
  deadline: string
  severity: 'high' | 'medium' | 'low'
  links?: Array<{ label: string; url: string }>
}

type TodayActionsData = {
  city: string
  date: string
  updatedAt: string
  dataSource: 'gemini' | 'cache' | 'mock'
  stale: boolean
  ttlSeconds: number
  items: ActionItem[]
  disclaimer: string
}

function formatRelativeTime(isoString: string): string {
  try {
    const updated = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - updated.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins} 分钟前`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours} 小时前`
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays} 天前`
  } catch {
    return '未知'
  }
}

function getSeverityIcon(severity: string): string {
  if (severity === 'high') return '🔴'
  if (severity === 'medium') return '🟡'
  return '🟢'
}

export function TodayActions() {
  const [data, setData] = useState<TodayActionsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchActions = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_URL}/risk/today-actions?city=cupertino`, {
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache'
          }
        })
        
        if (res.ok) {
          const result = await res.json()
          setData(result)
        } else {
          console.error('Failed to fetch today actions:', res.status)
        }
      } catch (error) {
        console.error('Error fetching today actions:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchActions()
  }, [])

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-gray-900">🧠 今日必做 3 件事</h3>
        </div>
        <div className="text-sm text-gray-500">加载中...</div>
      </div>
    )
  }

  if (!data || !data.items || data.items.length === 0) {
    // Show mock data if empty
    const mockItems: ActionItem[] = [
      {
        title: "检查 401(k) rollover 截止时间",
        why: "避免错过 60 天窗口导致税务后果",
        action: "今天把旧账户的 rollover 流程和所需表格确认完",
        deadline: "60 天内",
        severity: "high",
        links: []
      }
    ]
    
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-gray-900">🧠 今日必做 3 件事</h3>
          <span className="text-xs text-gray-500">暂无重要事项</span>
        </div>
        <div className="space-y-3">
          {mockItems.map((item, idx) => (
            <div key={idx} className="border-l-2 border-gray-200 pl-3">
              <div className="flex items-start gap-2 mb-1">
                <span>{getSeverityIcon(item.severity)}</span>
                <span className="font-semibold text-gray-900 text-sm">{item.title}</span>
              </div>
              <p className="text-xs text-gray-600 mb-1">{item.why}</p>
              <p className="text-xs text-gray-700">
                <span className="text-green-600">✅ 建议：</span>
                {item.action}
              </p>
              {item.deadline && (
                <p className="text-xs text-gray-500 mt-1">
                  <span>⏰ 截止：</span>
                  {item.deadline}
                </p>
              )}
            </div>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t border-gray-100 flex justify-end">
          <Link href="/risk" className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            查看详情 →
          </Link>
        </div>
      </div>
    )
  }

  const items = data.items.slice(0, 3) // Ensure max 3 items
  const relativeTime = formatRelativeTime(data.updatedAt)
  const isStale = data.stale || data.dataSource === 'mock'

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-semibold text-gray-900">🧠 今日必做 3 件事</h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">更新于 {relativeTime}</span>
          {isStale && (
            <span className="text-xs text-gray-500 px-2 py-0.5 bg-gray-100 rounded">
              {data.dataSource === 'mock' ? 'Mock' : 'Stale'}
            </span>
          )}
        </div>
      </div>

      {/* Actions List */}
      <div className="space-y-3">
        {items.map((item, idx) => (
          <div key={idx} className="border-l-2 border-gray-200 pl-3">
            <div className="flex items-start gap-2 mb-1">
              <span className="text-sm">{getSeverityIcon(item.severity)}</span>
              <span className="font-semibold text-gray-900 text-sm">{item.title}</span>
            </div>
            <p className="text-xs text-gray-600 mb-1">{item.why}</p>
            <p className="text-xs text-gray-700">
              <span className="text-green-600">✅ 建议：</span>
              {item.action}
            </p>
            {item.deadline && item.deadline.trim() && (
              <p className="text-xs text-gray-500 mt-1">
                <span>⏰ 截止：</span>
                {item.deadline}
              </p>
            )}
            {item.links && item.links.length > 0 && (
              <div className="flex gap-2 mt-1">
                {item.links.map((link, linkIdx) => (
                  <a
                    key={linkIdx}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:text-blue-800 underline"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-3 pt-3 border-t border-gray-100 flex justify-end">
        <Link href="/risk" className="text-sm text-blue-600 hover:text-blue-800 font-medium">
          查看详情 →
        </Link>
      </div>
    </div>
  )
}

