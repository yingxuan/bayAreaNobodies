/**
 * Deals Carousel - (7) 遍地羊毛
 * Fast food / daily deals with images and savings
 */
'use client'

import { useState, useEffect } from 'react'
import { CarouselSection } from './CarouselSection'
import { getDealReadableTitle, getDealSaveText } from '../lib/dealFormat'
import { getDealImage } from '../lib/dealImage'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type DealCardProps = {
  deal: any
}

function DealCard({ deal }: DealCardProps) {
  const { src: imageSrc } = getDealImage(deal)
  const titleCN = getDealReadableTitle(deal)
  const saveText = getDealSaveText(deal)
  
  // Determine category
  const dealText = `${deal.title || ''} ${deal.description || ''}`.toLowerCase()
  let category = '日用品'
  if (dealText.includes('burger') || dealText.includes('subway') || dealText.includes('快餐') || 
      dealText.includes('food') || dealText.includes('restaurant') || dealText.includes('meal')) {
    category = '快餐'
  }
  
  // Determine conditions
  const conditions: string[] = []
  if (dealText.includes('bogo') || dealText.includes('buy one get one')) {
    conditions.push('BOGO')
  } else if (dealText.includes('clip') || deal.code) {
    conditions.push('需 Clip')
  } else if (dealText.includes('app')) {
    conditions.push('需 App')
  } else {
    conditions.push('无门槛')
  }

  const handleClick = () => {
    if (deal.externalUrl) {
      window.open(deal.externalUrl, '_blank')
    } else if (deal.sourceUrl) {
      window.open(deal.sourceUrl, '_blank')
    } else if (deal.url) {
      window.open(deal.url, '_blank')
    }
  }

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 w-48 bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer"
    >
      {/* Image */}
      <div className="relative w-full h-32 bg-gray-100">
        <img
          src={imageSrc}
          alt={titleCN}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2YjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'
          }}
        />
      </div>
      
      {/* Content */}
      <div className="p-3">
        {/* Category badge */}
        <div className="mb-2">
          <span className={`text-xs px-2 py-0.5 rounded ${
            category === '快餐' 
              ? 'bg-orange-100 text-orange-700' 
              : 'bg-blue-100 text-blue-700'
          }`}>
            {category}
          </span>
        </div>
        
        {/* Title + Core deal */}
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-2">
          {titleCN}
        </h4>
        
        {/* Savings amount */}
        {saveText && (
          <div className="text-base font-bold text-green-600 mb-1">
            💰 {saveText.replace('可省 ', '')}
          </div>
        )}
        
        {/* Conditions */}
        <div className="text-xs text-gray-500">
          {conditions.join(' · ')}
        </div>
      </div>
    </div>
  )
}

export function DealsCarousel() {
  const [deals, setDeals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDeals()
  }, [])

  const fetchDeals = async () => {
    setLoading(true)
    try {
      const [foodDealsRes, retailDealsRes] = await Promise.all([
        fetch(`${API_URL}/deals/food?city=cupertino&limit=12`).catch(() => null),
        fetch(`${API_URL}/feeds/deals?limit=12`).catch(() => null)
      ])

      const allDeals: any[] = []

      if (foodDealsRes?.ok) {
        const foodData = await foodDealsRes.json()
        if (foodData.items) {
          allDeals.push(...foodData.items)
        }
      }

      if (retailDealsRes?.ok) {
        const retailData = await retailDealsRes.json()
        if (retailData.coupons) {
          allDeals.push(...retailData.coupons)
        }
      }

      // Deduplicate by title + source (merge same products)
      const seen = new Map<string, any>()
      allDeals.forEach(deal => {
        const key = `${deal.title || ''}_${deal.source || ''}`.toLowerCase()
        if (!seen.has(key)) {
          seen.set(key, deal)
        } else {
          // Merge: keep the one with better image or more info
          const existing = seen.get(key)
          if (!existing.image_url && deal.image_url) {
            seen.set(key, deal)
          }
        }
      })
      const uniqueDeals = Array.from(seen.values())

      // Prioritize fast food / daily goods, then shuffle
      const prioritized = uniqueDeals.sort((a, b) => {
        const aText = `${a.title || ''} ${a.description || ''}`.toLowerCase()
        const bText = `${b.title || ''} ${b.description || ''}`.toLowerCase()
        const aIsFood = aText.includes('burger') || aText.includes('subway') || aText.includes('快餐')
        const bIsFood = bText.includes('burger') || bText.includes('subway') || bText.includes('快餐')
        if (aIsFood && !bIsFood) return -1
        if (!aIsFood && bIsFood) return 1
        return Math.random() - 0.5
      })
      setDeals(prioritized.slice(0, 12))
    } catch (error) {
      console.error('Error fetching deals:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    fetchDeals()
  }

  if (loading) {
    return (
      <CarouselSection title="💰 遍地羊毛" viewMoreHref="/deals">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex-shrink-0 w-48 h-40 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </CarouselSection>
    )
  }

  if (deals.length === 0) {
    return null
  }

  return (
    <CarouselSection
      title="💰 遍地羊毛"
      viewMoreHref="/deals"
      onRefresh={handleRefresh}
      showRefresh={true}
    >
      {deals.map((deal, idx) => (
        <DealCard key={deal.id || deal.source_id || idx} deal={deal} />
      ))}
    </CarouselSection>
  )
}

