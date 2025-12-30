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
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-4 h-full flex flex-col w-full max-w-full ${className}`}>
      {/* Header - Consistent style */}
      <div className="mb-2 min-h-[32px] flex items-center justify-between gap-2">
        <h2 className="text-base font-bold text-gray-900 truncate">{title}</h2>
        {viewMoreHref && (
          <Link href={viewMoreHref} className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap flex-shrink-0">
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

