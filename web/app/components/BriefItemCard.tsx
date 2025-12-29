'use client'

import Link from 'next/link'
import { DailyBriefItem } from '../lib/dailyBrief'

interface BriefItemCardProps {
  item: DailyBriefItem
  size?: 'large' | 'small'
}

export function BriefItemCard({ item, size = 'small' }: BriefItemCardProps) {
  const isLarge = size === 'large'
  
  return (
    <Link
      href={item.href}
      className={`block border border-gray-200 rounded-lg hover:shadow-md transition-all ${
        isLarge ? 'p-6 md:p-8' : 'p-4'
      }`}
    >
      <div className={`flex items-start gap-${isLarge ? '4' : '3'}`}>
        <div className={`flex-shrink-0 ${isLarge ? 'text-3xl' : 'text-2xl'}`}>{item.icon}</div>
        <div className="flex-1 min-w-0">
          <div className={`flex items-center gap-2 mb-${isLarge ? '2' : '1'} flex-wrap`}>
            <h3 className={`font-semibold text-gray-900 ${isLarge ? 'text-lg' : 'text-base'}`}>
              {item.title}
            </h3>
            {item.tags && item.tags.length > 0 && (
              <div className="flex gap-1 flex-wrap">
                {item.tags.map((tag, idx) => {
                  const isSpecialTag = tag.includes('✅') || tag.includes('🧪') || tag.includes('⚠️') || tag.includes('🔥')
                  return (
                    <span
                      key={idx}
                      className={`px-2 py-0.5 text-xs rounded ${
                        isSpecialTag
                          ? 'bg-green-50 text-green-700'
                          : 'bg-blue-50 text-blue-700'
                      }`}
                    >
                      {tag}
                    </span>
                  )
                })}
              </div>
            )}
          </div>
          <p className={`text-gray-600 mb-3 ${isLarge ? 'text-base line-clamp-3' : 'text-sm line-clamp-2'}`}>
            {item.summary}
          </p>
          <span className={`inline-block font-medium text-blue-600 ${isLarge ? 'text-base' : 'text-sm'}`}>
            {item.ctaText} →
          </span>
        </div>
      </div>
    </Link>
  )
}

