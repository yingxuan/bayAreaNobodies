/**
 * Entry Card - Layer 3: Entry Points
 * Generic entry card component for 6 entry points
 * No lists, only one-line summary + CTA
 */
'use client'

import Link from 'next/link'

type EntryCardProps = {
  icon: string
  title: string
  summary: string
  href: string
  onClick?: () => void
  imageUrl?: string
  badge?: string
  onRefresh?: () => void
  showRefresh?: boolean
  highlightReason?: string // e.g., "招牌流沙包" or "⭐ 4.6 · Cupertino" or "BOGO · 可省 $8"
  imageHeight?: 'normal' | 'large' // Control image size
}

export function EntryCard({ icon, title, summary, href, onClick, imageUrl, badge, onRefresh, showRefresh, highlightReason, imageHeight = 'normal' }: EntryCardProps) {
  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault()
      onClick()
    }
  }

  const handleRefresh = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (onRefresh) {
      onRefresh()
    }
  }

  const imageHeightClass = imageHeight === 'large' ? 'h-32' : 'h-24'

  return (
    <Link
      href={href}
      onClick={handleClick}
      className="block bg-white rounded-xl shadow-sm p-4 border border-gray-200 hover:shadow-md transition-all hover:border-blue-300 relative"
    >
      {/* Refresh button (top right, more prominent) */}
      {showRefresh && onRefresh && (
        <button
          onClick={handleRefresh}
          className="absolute top-2 right-2 p-2 rounded-full bg-white shadow-sm hover:bg-gray-50 hover:shadow-md transition-all border border-gray-200"
          title="换一个"
          aria-label="换一个"
        >
          <span className="text-base">🔄</span>
        </button>
      )}
      
      {/* Image first (if available, larger) */}
      {imageUrl && (
        <div className={`mb-3 rounded-lg overflow-hidden ${imageHeightClass}`}>
          <img
            src={imageUrl}
            alt={title}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        </div>
      )}
      
      <div className="flex items-start gap-2">
        {/* Icon */}
        <div className="flex-shrink-0 text-xl">{icon}</div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-bold text-gray-900 text-base leading-tight">{title}</h3>
            {badge && (
              <span className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded font-medium">
                {badge}
              </span>
            )}
          </div>
          
          {/* Summary */}
          <p className="text-sm text-gray-700 line-clamp-2 mb-1.5">
            {summary}
          </p>
          
          {/* Highlight reason (why recommended) */}
          {highlightReason && (
            <p className="text-xs text-gray-600 mb-2">
              {highlightReason}
            </p>
          )}
          
          {/* CTA */}
          <div className="text-xs text-blue-600 font-medium">
            查看 →
          </div>
        </div>
      </div>
    </Link>
  )
}

