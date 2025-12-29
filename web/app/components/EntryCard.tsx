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
}

export function EntryCard({ icon, title, summary, href, onClick, imageUrl, badge }: EntryCardProps) {
  const handleClick = (e: React.MouseEvent) => {
    if (onClick) {
      e.preventDefault()
      onClick()
    }
  }

  return (
    <Link
      href={href}
      onClick={handleClick}
      className="block bg-white rounded-xl shadow-sm p-4 border border-gray-200 hover:shadow-md transition-all hover:border-blue-300"
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 text-2xl">{icon}</div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 text-base">{title}</h3>
            {badge && (
              <span className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded">
                {badge}
              </span>
            )}
          </div>
          
          {/* Summary (one line) */}
          <p className="text-sm text-gray-700 line-clamp-2 mb-2">
            {summary}
          </p>
          
          {/* Image (if available, small) */}
          {imageUrl && (
            <div className="mb-2 rounded-lg overflow-hidden">
              <img
                src={imageUrl}
                alt={title}
                className="w-full h-24 object-cover"
                onError={(e) => {
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
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

