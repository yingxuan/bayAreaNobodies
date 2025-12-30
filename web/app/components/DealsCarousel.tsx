/**
 * Deals Carousel - (7) 遍地羊毛
 * Fast food / daily deals with images and savings
 * Now with intelligent filtering and scoring
 */
'use client'

import { useState, useEffect } from 'react'
import { SharedCarousel } from './SharedCarousel'
import { getDealImage } from '../lib/dealImage'
import { processDeals, NormalizedDeal, scoreDeal } from '../lib/deals/filterScoreDeals'
import { MAX_ITEMS_PER_CATEGORY, MIN_ITEMS_TO_SHOW } from '../lib/deals/dealsConfig'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type DealCardProps = {
  deal: NormalizedDeal
}

function DealCard({ deal }: DealCardProps) {
  const { src: imageSrc } = getDealImage(deal.originalData)
  
  // Get category display name
  const categoryCN = deal.category === 'fast_food' ? '快餐' : 
                     deal.category === 'grocery' ? '日用品' : 'Apps'
  
  // Format merchant + offer highlight
  const merchantDisplay = deal.merchant || '精选'
  const valueDisplay = deal.price_or_value_text || 
                      (deal.estimated_value_usd ? `$${deal.estimated_value_usd.toFixed(0)}` : '')
  
  // Redemption method
  const redemptionText = deal.requires_app === true ? '需App' :
                        deal.requires_app === false ? '无需App' :
                        deal.redemption_type === 'app' ? '需App' :
                        deal.redemption_type === 'online' ? '在线' :
                        deal.redemption_type === 'in_store' ? '店内' :
                        deal.redemption_type === 'subscription' ? '订阅' : ''

  // Check if expiring soon
  const isExpiringSoon = deal.expiry_date && 
    (deal.expiry_date.getTime() - new Date().getTime()) <= 48 * 60 * 60 * 1000 &&
    (deal.expiry_date.getTime() - new Date().getTime()) > 0

  const handleClick = () => {
    if (deal.url) {
      window.open(deal.url, '_blank')
    }
  }

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 min-w-[240px] sm:min-w-[260px] bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start flex flex-col"
    >
      {/* Image */}
      <div className="relative w-full h-32 bg-gray-100 flex-shrink-0">
        <img
          src={imageSrc}
          alt={deal.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2YjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'
          }}
        />
      </div>
      
      {/* Content */}
      <div className="p-3 flex flex-col flex-1">
        {/* Merchant + Value highlight */}
        <div className="mb-1.5">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs font-semibold text-gray-900">{merchantDisplay}</span>
            {valueDisplay && (
              <span className="text-xs font-bold text-green-600">• {valueDisplay}</span>
            )}
            {isExpiringSoon && (
              <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded">限时</span>
            )}
          </div>
        </div>
        
        {/* Title */}
        <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-2 flex-1">
          {deal.title}
        </h4>
        
        {/* Redemption method + Source badge */}
        <div className="flex items-center justify-between gap-2 mt-auto">
          <div className="text-xs text-gray-500">
            {redemptionText && <span>{redemptionText}</span>}
          </div>
          <div className="text-xs text-gray-400 truncate max-w-[100px]">
            {deal.source.replace('www.', '').split('.')[0]}
          </div>
        </div>
      </div>
    </div>
  )
}

type TabType = 'fastfood' | 'grocery' | 'apps'

export function DealsCarousel() {
  const [activeTab, setActiveTab] = useState<TabType>('fastfood')
  const [allDeals, setAllDeals] = useState<{
    fastfood: NormalizedDeal[]
    grocery: NormalizedDeal[]
    apps: NormalizedDeal[]
  }>({
    fastfood: [],
    grocery: [],
    apps: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDeals()
  }, [])

  const fetchDeals = async () => {
    setLoading(true)
    try {
      const [foodDealsRes, retailDealsRes] = await Promise.all([
        fetch(`${API_URL}/deals/food?city=cupertino&limit=30`).catch(() => null),
        fetch(`${API_URL}/feeds/deals?limit=50`).catch(() => null)
      ])

      const allDealsList: any[] = []

      if (foodDealsRes?.ok) {
        const foodData = await foodDealsRes.json()
        if (foodData.items) {
          allDealsList.push(...foodData.items)
        }
      }

      if (retailDealsRes?.ok) {
        const retailData = await retailDealsRes.json()
        if (retailData.coupons) {
          allDealsList.push(...retailData.coupons)
        }
      }

      // Process deals: normalize, filter, deduplicate, score, rank
      const processed = processDeals(allDealsList)

      // Map categories (fast_food -> fastfood for state)
      // Limit each category to MAX_ITEMS_PER_CATEGORY
      setAllDeals({
        fastfood: processed.fast_food.slice(0, MAX_ITEMS_PER_CATEGORY),
        grocery: processed.grocery.slice(0, MAX_ITEMS_PER_CATEGORY),
        apps: processed.apps.slice(0, MAX_ITEMS_PER_CATEGORY)
      })
    } catch (error) {
      console.error('Error fetching deals:', error)
    } finally {
      setLoading(false)
    }
  }

  const currentDeals = allDeals[activeTab]

  if (loading) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-gray-900">💰 遍地羊毛</h3>
        </div>
        <div className="flex gap-2 border-b border-gray-200">
          {['快餐', '日用品', 'Apps'].map((tab) => (
            <div key={tab} className="px-3 py-2 text-sm text-gray-500">
              {tab}
            </div>
          ))}
        </div>
        <div className="overflow-x-auto scrollbar-hide">
          <div className="flex gap-3 pb-1">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex-shrink-0 w-48 h-40 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  // Don't render if no deals in any category
  if (allDeals.fastfood.length === 0 && allDeals.grocery.length === 0 && allDeals.apps.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold text-gray-900 truncate">💰 遍地羊毛</h3>
        <a href="/deals" className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap flex-shrink-0">
          查看更多 →
        </a>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('fastfood')}
          className={`px-3 py-2 text-sm font-medium transition-colors ${
            activeTab === 'fastfood'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          快餐 {allDeals.fastfood.length > 0 && `(${allDeals.fastfood.length})`}
        </button>
        <button
          onClick={() => setActiveTab('grocery')}
          className={`px-3 py-2 text-sm font-medium transition-colors ${
            activeTab === 'grocery'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          日用品 {allDeals.grocery.length > 0 && `(${allDeals.grocery.length})`}
        </button>
        <button
          onClick={() => setActiveTab('apps')}
          className={`px-3 py-2 text-sm font-medium transition-colors ${
            activeTab === 'apps'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Apps {allDeals.apps.length > 0 && `(${allDeals.apps.length})`}
        </button>
      </div>

      {/* Carousel Content - Horizontal scroll on mobile */}
      {currentDeals.length >= MIN_ITEMS_TO_SHOW ? (
        <SharedCarousel cardWidth={240} gap={12} maxVisible={MAX_ITEMS_PER_CATEGORY} className="w-full">
          {currentDeals.map((deal) => (
            <DealCard key={deal.id} deal={deal} />
          ))}
        </SharedCarousel>
      ) : currentDeals.length > 0 ? (
        <div className="text-xs text-gray-500 py-4 text-center">
          暂无高质量羊毛
        </div>
      ) : (
        <div className="text-xs text-gray-500 py-4 text-center">
          暂无{activeTab === 'fastfood' ? '快餐' : activeTab === 'grocery' ? '日用品' : 'Apps'}优惠
        </div>
      )}
    </div>
  )
}

