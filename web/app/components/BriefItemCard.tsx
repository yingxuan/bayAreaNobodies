'use client'

import Link from 'next/link'
import { DailyBriefItem } from '../lib/dailyBrief'

export function BriefItemCard({ item }: { item: DailyBriefItem }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <div className="text-2xl flex-shrink-0">{item.icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900">{item.title}</h3>
            {item.tags && item.tags.length > 0 && (
              <div className="flex gap-1 flex-wrap">
                {item.tags.map((tag, idx) => {
                  // Special styling for certain tags
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
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{item.summary}</p>
          <Link
            href={item.href}
            className="inline-block px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
          >
            {item.ctaText} →
          </Link>
        </div>
      </div>
    </div>
  )
}

