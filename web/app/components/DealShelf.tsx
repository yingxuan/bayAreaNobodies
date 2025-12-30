/**
 * Deal Shelf - Unified high-quality deal carousel
 * Silicon Valley tech worker focused, smart ranking, TOP 3 highlight
 */
'use client'

import { useState, useEffect, useRef } from 'react'
import { processUnifiedDeals, markTopDeals } from '../lib/deals/unifiedDealProcessing'
import { NormalizedDeal, normalizeDeal } from '../lib/deals/filterScoreDeals'
import { trackDealClick, scoreSVDeal } from '../lib/deals/svDealScoring'
import { getDealWebsiteImage, getCachedMetadata } from '../lib/deals/dealMetadata'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type ScoredDeal = NormalizedDeal & { isTop3: boolean; score: number }

type DealCardProps = {
  deal: ScoredDeal
  onImageLoad?: (url: string, imageUrl: string) => void
}

function DealCard({ deal, onImageLoad }: DealCardProps) {
  const [imageUrl, setImageUrl] = useState<string>('')
  const [isLoadingImage, setIsLoadingImage] = useState(true)

  useEffect(() => {
    // Get placeholder immediately
    getDealWebsiteImage(deal.url).then(placeholder => {
      setImageUrl(placeholder)
      setIsLoadingImage(true)
    })
    
    // Try to get cached metadata
    const cached = getCachedMetadata(deal.url)
    if (cached?.image) {
      setImageUrl(cached.image)
      setIsLoadingImage(false)
      if (onImageLoad) {
        onImageLoad(deal.url, cached.image)
      }
    } else {
      // Listen for metadata loaded event
      const handleMetadataLoaded = (e: CustomEvent) => {
        if (e.detail.url === deal.url && e.detail.image) {
          setImageUrl(e.detail.image)
          setIsLoadingImage(false)
          if (onImageLoad) {
            onImageLoad(deal.url, e.detail.image)
          }
        }
      }
      
      window.addEventListener('dealMetadataLoaded', handleMetadataLoaded as EventListener)
      
      return () => {
        window.removeEventListener('dealMetadataLoaded', handleMetadataLoaded as EventListener)
      }
    }
  }, [deal.url, onImageLoad])

  const handleClick = () => {
    trackDealClick(deal)
    if (deal.url) {
      window.open(deal.url, '_blank')
    }
  }

  const valueDisplay = deal.price_or_value_text || 
                      (deal.estimated_value_usd ? `$${deal.estimated_value_usd.toFixed(0)}` : '')
  
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

  // Extract domain for display
  const domain = deal.source.replace('www.', '').split('.')[0]

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 min-w-[240px] lg:min-w-[280px] bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer snap-start flex flex-col relative"
    >
      {/* TOP 3 Badge */}
      {deal.isTop3 && (
        <div className="absolute top-2 left-2 z-10 px-2 py-0.5 bg-orange-500 text-white text-xs font-bold rounded shadow-md">
          🔥 今日最值
        </div>
      )}
      
      {/* Image - aspect-[16/10] */}
      <div className="relative w-full aspect-[16/10] bg-gray-100 flex-shrink-0">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={deal.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              // Fallback to placeholder on error
              e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMzIwIiBoZWlnaHQ9IjE4MCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM2YjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'
            }}
          />
        ) : (
          <div className="w-full h-full bg-gray-200 animate-pulse" />
        )}
      </div>
      
      {/* Content */}
      <div className="p-3 flex flex-col flex-1">
        {/* Value pill - prominent */}
        {valueDisplay && (
          <div className="mb-1.5">
            <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded">
              {valueDisplay}
            </span>
            {isExpiringSoon && (
              <span className="ml-1.5 inline-block px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                限时
              </span>
            )}
          </div>
        )}
        
        {/* Title - line-clamp-2 */}
        <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-2 flex-1">
          {deal.title}
        </h4>
        
        {/* Meta row: source + redemption + time */}
        <div className="flex items-center justify-between gap-2 mt-auto text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            {redemptionText && <span>{redemptionText}</span>}
            <span className="text-gray-400">•</span>
            <span className="truncate max-w-[100px]">{domain}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export function DealShelf() {
  const [deals, setDeals] = useState<ScoredDeal[]>([])
  const [loading, setLoading] = useState(true)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchDeals()
  }, [])

  const fetchDeals = async () => {
    setLoading(true)
    try {
      // Fetch from all deal sources
      const [foodDealsRes, retailDealsRes, huarenDealsRes] = await Promise.all([
        fetch(`${API_URL}/deals/food?city=cupertino&limit=20`).catch(() => null), // API max limit is 20
        fetch(`${API_URL}/feeds/deals?limit=50`).catch(() => null),
        fetch(`${API_URL}/deals/huaren?limit=30`).catch(() => null)
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

      if (huarenDealsRes?.ok) {
        const huarenData = await huarenDealsRes.json()
        if (huarenData.items) {
          allDealsList.push(...huarenData.items)
        }
      }

      // Debug: log raw data
      console.log('DealShelf: Raw deals fetched', {
        food: foodDealsRes?.ok ? 'ok' : 'failed',
        retail: retailDealsRes?.ok ? 'ok' : 'failed',
        huaren: huarenDealsRes?.ok ? 'ok' : 'failed',
        totalRaw: allDealsList.length
      })

      // Process: normalize, deduplicate, filter, score, rank
      const processed = processUnifiedDeals(allDealsList)
      
      console.log('DealShelf: Processed deals', {
        processed: processed.length,
        raw: allDealsList.length
      })
      
      // Mark TOP 3 and add scores
      const topMarked = markTopDeals(processed).map(deal => ({
        ...deal,
        score: scoreSVDeal(deal)
      }))
      
      // If no processed deals, try to show at least some raw deals (fallback)
      if (topMarked.length === 0 && allDealsList.length > 0) {
        console.warn('DealShelf: No deals passed filtering, showing raw deals as fallback')
        // Try to normalize at least first few raw deals without strict filtering
        const fallbackDeals = allDealsList.slice(0, 6).map((deal, idx) => {
          try {
            const normalized = normalizeDeal(deal)
            if (normalized) {
              return {
                ...normalized,
                isTop3: idx < 3,
                score: scoreSVDeal(normalized)
              }
            }
          } catch (e) {
            console.error('Error normalizing fallback deal:', e)
          }
          return null
        }).filter((deal): deal is ScoredDeal => deal !== null)
        
        setDeals(fallbackDeals)
      } else {
        // Limit to top 10-12 for homepage
        setDeals(topMarked.slice(0, 12))
      }
    } catch (error) {
      console.error('Error fetching deals:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleImageLoad = (url: string, imageUrl: string) => {
    // Image loaded, could trigger re-render if needed
  }

  if (loading) {
    return (
      <div className="flex gap-3 overflow-x-auto scroll-smooth scrollbar-hide pb-2">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex-shrink-0 min-w-[240px] lg:min-w-[280px] bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="w-full aspect-[16/10] bg-gray-100 animate-pulse" />
            <div className="p-3">
              <div className="h-4 bg-gray-100 rounded animate-pulse mb-2" />
              <div className="h-3 bg-gray-100 rounded animate-pulse w-2/3" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (deals.length === 0) {
    return (
      <div className="text-xs text-gray-500 py-4 text-center">
        暂无高质量羊毛
      </div>
    )
  }

  return (
    <div className="relative">
      {/* Carousel - horizontal scroll */}
      <div
        ref={scrollContainerRef}
        className="flex gap-3 overflow-x-auto scroll-smooth scrollbar-hide pb-2"
      >
        {deals.map((deal) => (
          <DealCard key={deal.id} deal={deal} onImageLoad={handleImageLoad} />
        ))}
      </div>
    </div>
  )
}

