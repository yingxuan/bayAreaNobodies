'use client'

import { useState, ReactNode } from 'react'

interface CollapsibleSectionProps {
  title: string
  summary: string
  children: ReactNode
  defaultCollapsed?: boolean
}

export function CollapsibleSection({
  title,
  summary,
  children,
  defaultCollapsed = true
}: CollapsibleSectionProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed)

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">{title.includes('资产') ? '💼' : ''}</span>
          <div className="text-left">
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            <p className="text-sm text-gray-600">{summary}</p>
          </div>
        </div>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform ${isCollapsed ? '' : 'rotate-180'}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {!isCollapsed && (
        <div className="px-6 pb-6">
          {children}
        </div>
      )}
    </div>
  )
}

