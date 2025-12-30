/**
 * Standard Card - Consistent styling for all cards
 * Ensures uniform padding, header style, and footer actions
 */
'use client'

import Link from 'next/link'

type StandardCardProps = {
  title: string
  viewMoreHref?: string
  children: React.ReactNode
  className?: string
}

export function StandardCard({ title, viewMoreHref, children, className = '' }: StandardCardProps) {
  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-3 h-full flex flex-col ${className}`}>
      {/* Header - Consistent style */}
      <div className="mb-2 min-h-[36px] flex items-center justify-between">
        <h2 className="text-lg font-bold text-gray-900">{title}</h2>
        {viewMoreHref && (
          <Link href={viewMoreHref} className="text-xs text-blue-600 hover:text-blue-700">
            更多 →
          </Link>
        )}
      </div>

      {/* Content */}
      <div className="flex-1">
        {children}
      </div>
    </div>
  )
}

