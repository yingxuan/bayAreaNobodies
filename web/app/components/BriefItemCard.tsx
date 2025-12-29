'use client'

import Link from 'next/link'
import { DailyBriefItem } from '../lib/dailyBrief'

interface BriefItemCardProps {
  item: DailyBriefItem
  size?: 'large' | 'small'
}

export function BriefItemCard({ item, size = 'small' }: BriefItemCardProps) {
  const isLarge = size === 'large'
  const isRiskCard = item.id === 'risk'
  const hasValidRisk = item.title.includes('风险提醒') && item.title.includes('（') && item.title.includes('）')
  
  // Risk card styling: low presence when no risks, higher contrast when has risks
  const riskCardClasses = isRiskCard
    ? hasValidRisk
      ? 'border-yellow-300 bg-yellow-50 hover:bg-yellow-100' // State B: Has risks
      : 'border-gray-200 bg-gray-50 hover:bg-gray-100 opacity-75' // State A: No risks (low presence)
    : ''
  
  return (
    <Link
      href={item.href}
      className={`block border rounded-lg hover:shadow-md transition-all ${
        isLarge ? 'p-6 md:p-8' : 'p-4'
      } ${riskCardClasses || 'border-gray-200'}`}
    >
      <div className={`flex items-start ${isLarge ? 'gap-4' : 'gap-3'}`}>
        <div className={`flex-shrink-0 ${isLarge ? 'text-3xl' : 'text-2xl'}`}>{item.icon}</div>
        <div className="flex-1 min-w-0">
          <div className={`flex items-center gap-2 ${isLarge ? 'mb-2' : 'mb-1'} flex-wrap`}>
            <h3 className={`font-semibold text-gray-900 ${isLarge ? 'text-lg' : 'text-base'}`}>
              {item.title}
            </h3>
            {item.tags && item.tags.length > 0 && (
              <div className="flex gap-1 flex-wrap">
                {item.tags.map((tag, idx) => {
                  const isSpecialTag = tag.includes('✅') || tag.includes('🧪') || tag.includes('⚠️') || tag.includes('🔥')
                  const isRiskTag = tag.includes('🔴') || tag.includes('🟡') || tag.includes('🟢')
                  return (
                    <span
                      key={idx}
                      className={`px-2 py-0.5 text-xs rounded ${
                        isRiskTag
                          ? tag.includes('🔴')
                            ? 'bg-red-50 text-red-700'
                            : tag.includes('🟡')
                            ? 'bg-yellow-50 text-yellow-700'
                            : 'bg-green-50 text-green-700'
                          : isSpecialTag
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
          <span className={`inline-block font-medium ${isRiskCard && !hasValidRisk ? 'text-gray-500' : 'text-blue-600'} ${isLarge ? 'text-base' : 'text-sm'}`}>
            {item.ctaText} →
          </span>
        </div>
      </div>
    </Link>
  )
}

