/**
 * Carousel Section - Generic carousel wrapper
 * Used for: 吃点好的, 肥宅快乐水, 遍地羊毛, 打发时间, 北美八卦
 */
'use client'

import { ReactNode } from 'react'
import Link from 'next/link'

type CarouselSectionProps = {
  title: string
  subtitle?: string
  viewMoreHref?: string
  onRefresh?: () => void
  showRefresh?: boolean
  children: ReactNode
}

export function CarouselSection({
  title,
  subtitle,
  viewMoreHref,
  onRefresh,
  showRefresh = false,
  children
}: CarouselSectionProps) {
  return (
    <div className="space-y-2">
      {/* Header - Only show if title is provided */}
      {(title || viewMoreHref || (showRefresh && onRefresh)) && (
        <div className="flex items-center justify-between">
          <div>
            {title && (
              <h3 className="text-base font-bold text-gray-900">{title}</h3>
            )}
            {subtitle && (
              <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {showRefresh && onRefresh && (
              <button
                onClick={onRefresh}
                className="text-xs text-gray-600 hover:text-gray-900 px-1.5 py-0.5 rounded hover:bg-gray-100"
                title="换一批"
              >
                换一批
              </button>
            )}
            {viewMoreHref && (
              <Link href={viewMoreHref} className="text-xs text-blue-600 hover:text-blue-700">
                查看更多 →
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Carousel Content */}
      <div className="overflow-x-auto scrollbar-hide">
        <div className="flex gap-3 pb-1">
          {children}
        </div>
      </div>
    </div>
  )
}

