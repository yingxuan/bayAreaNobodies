/**
 * Collapsible Section - For low-priority content
 * Collapsed by default, can be expanded
 */
'use client'

import { useState } from 'react'

type CollapsibleSectionProps = {
  title: string
  children: React.ReactNode
  defaultCollapsed?: boolean
  className?: string
}

export function CollapsibleSection({ 
  title, 
  children, 
  defaultCollapsed = true,
  className = '' 
}: CollapsibleSectionProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed)

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 ${className}`}>
      {/* Header - Always visible */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <h2 className="text-base font-bold text-gray-900">{title}</h2>
        <span className="text-xs text-gray-500">
          {isCollapsed ? '展开' : '收起'}
        </span>
      </button>

      {/* Content - Collapsible */}
      {!isCollapsed && (
        <div className="px-3 pb-3">
          {children}
        </div>
      )}
    </div>
  )
}

