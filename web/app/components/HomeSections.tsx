'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { CollapsibleSection } from './CollapsibleSection'
import { ViewMoreButton } from './ViewMoreButton'
import { HOME_LIMITS } from '../lib/constants'
import { generateSlug } from '../lib/slug'
import { translateDealTitle } from '../lib/i18n'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Lightweight Restaurant Grid (4 items only, fixed height)
export function HomeRestaurantSection({ cuisineType, title }: { cuisineType: string, title: string }) {
  const [restaurants, setRestaurants] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchRestaurants()
  }, [cuisineType])

  const fetchRestaurants = async () => {
    setLoading(true)
    try {
      // Client component - caching handled by server
      const res = await fetch(`${API_URL}/food/restaurants?cuisine_type=${cuisineType}&limit=${HOME_LIMITS.RESTAURANT}`)
      if (res.ok) {
        const data = await res.json()
        setRestaurants(data.restaurants || [])
      }
    } catch (error) {
      console.error('Error fetching restaurants:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-xl font-bold mb-4">{title}</h3>
        <div className="text-center py-4">加载中...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold">{title}</h3>
        <ViewMoreButton href="/food" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {restaurants.map((restaurant) => (
          <Link
            key={restaurant.id}
            href={`/eat/cupertino/${generateSlug(restaurant.name || '')}-${restaurant.id}`}
            className="bg-gray-50 rounded-lg overflow-hidden hover:shadow-md transition-shadow h-full flex flex-col"
          >
            {restaurant.photo_url && (
              <img
                src={restaurant.photo_url}
                alt={restaurant.name}
                className="w-full h-40 object-cover"
              />
            )}
            <div className="p-4 flex-1 flex flex-col">
              <h4 className="font-semibold text-gray-900 mb-1 line-clamp-1">{restaurant.name}</h4>
              <p className="text-sm text-gray-600 mb-2 line-clamp-1 flex-1">{restaurant.address}</p>
              <div className="flex items-center gap-2 mt-auto">
                {restaurant.rating && (
                  <span className="text-sm text-yellow-600">⭐ {restaurant.rating}</span>
                )}
                {restaurant.user_ratings_total && (
                  <span className="text-xs text-gray-500">({restaurant.user_ratings_total})</span>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

// Lightweight Deals List (6 items only)
export function HomeDealsSection() {
  const [deals, setDeals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDeals()
  }, [])

  const fetchDeals = async () => {
    setLoading(true)
    try {
      // Client component - caching handled by server
      const res = await fetch(`${API_URL}/feeds/deals?limit=${HOME_LIMITS.DEALS}`)
      if (res.ok) {
        const data = await res.json()
        setDeals(data.coupons || [])
      }
    } catch (error) {
      console.error('Error fetching deals:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-xl font-bold mb-4">羊毛专区</h3>
        <div className="text-center py-4">加载中...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold">羊毛专区</h3>
        <ViewMoreButton href="/deals" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {deals.slice(0, HOME_LIMITS.DEALS).map((deal) => (
          <Link
            key={deal.id}
            href={`/deals/${deal.source || 'unknown'}/${generateSlug(deal.title || deal.description || '')}-${deal.id}`}
            className="block p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <h4 className="font-semibold text-gray-900 mb-1 line-clamp-1">{translateDealTitle(deal.title || deal.description || '')}</h4>
            <p className="text-sm text-gray-600 line-clamp-2">{deal.description || deal.snippet}</p>
            {deal.category && (
              <span className="inline-block mt-2 px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">
                {deal.category}
              </span>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}

// Lightweight Gossip List (5 items only)
export function HomeGossipSection() {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchGossip()
  }, [])

  const fetchGossip = async () => {
    setLoading(true)
    try {
      // Client component - caching handled by server
      const res = await fetch(`${API_URL}/feeds/gossip?limit=${HOME_LIMITS.GOSSIP}`)
      if (res.ok) {
        const data = await res.json()
        setArticles(data.articles || [])
      }
    } catch (error) {
      console.error('Error fetching gossip:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-xl font-bold mb-4">八卦专区</h3>
        <div className="text-center py-4">加载中...</div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold">八卦专区</h3>
        <ViewMoreButton href="/gossip" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {articles.slice(0, HOME_LIMITS.GOSSIP).map((article) => (
          <Link
            key={article.id}
            href={`/posts/${article.source || 'unknown'}/${generateSlug(article.title || '')}-${article.id}`}
            className="block p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <h4 className="font-semibold text-gray-900 mb-1 line-clamp-1">{article.title}</h4>
            <p className="text-sm text-gray-600 line-clamp-2">{article.snippet || article.summary}</p>
            {article.tags && Array.isArray(article.tags) && article.tags.length > 0 && (
              <div className="flex gap-1 mt-2 flex-wrap">
                {article.tags.slice(0, 2).map((tag: string, idx: number) => (
                  <span key={idx} className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  )
}

// Portfolio Collapsible Section
export function HomePortfolioSection() {
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPortfolio()
  }, [])

  const loadPortfolio = async () => {
    setLoading(true)
    try {
      // Client component - caching handled by server
      const res = await fetch(`${API_URL}/portfolio/db-summary`)
      if (res.ok) {
        const data = await res.json()
        setPortfolioData(data)
      }
    } catch (error) {
      console.error('Error loading portfolio:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !portfolioData) {
    return (
      <CollapsibleSection
        title="💼 我的资产"
        summary="加载中..."
        defaultCollapsed={true}
      >
        <div className="text-center py-4">加载中...</div>
      </CollapsibleSection>
    )
  }

  // Header: No numbers, only title + hint text (total value already shown in TodayBrief)
  const summary = "展开查看持仓"
  
  // For expanded content, we still need these values
  const dayGain = portfolioData.day_gain || 0
  const dayGainPercent = portfolioData.day_gain_percent || 0
  const gainSign = dayGain >= 0 ? '+' : ''

  return (
    <CollapsibleSection
      title="💼 我的资产"
      summary={summary}
      defaultCollapsed={true}
    >
      <div className="space-y-4">
        {/* Portfolio Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">总资产</div>
            <div className="text-xl font-semibold text-gray-900">
              ${(portfolioData.total_value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">今日收益</div>
            <div className={`text-xl font-semibold ${dayGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {gainSign}${Math.abs(dayGain).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className={`text-sm ${dayGainPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ({gainSign}{Math.abs(dayGainPercent).toFixed(2)}%)
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">总收益</div>
            <div className={`text-xl font-semibold ${portfolioData.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {portfolioData.total_pnl >= 0 ? '+' : ''}${Math.abs(portfolioData.total_pnl || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        {/* Holdings Table (simplified) */}
        {portfolioData.holdings && portfolioData.holdings.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">代码</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">价格</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">数量</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">市值</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {portfolioData.holdings.slice(0, 10).map((holding: any) => (
                  <tr key={holding.ticker}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{holding.ticker}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">${holding.current_price?.toFixed(2) || 'N/A'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{holding.quantity || 0}</td>
                    <td className="px-4 py-3 text-sm text-gray-900">${(holding.value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {portfolioData.holdings.length > 10 && (
              <div className="mt-4 text-center">
                <Link href="/wealth" className="text-sm text-blue-600 hover:text-blue-800">
                  查看全部持仓 ({portfolioData.holdings.length} 只) →
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </CollapsibleSection>
  )
}

