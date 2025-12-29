'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { generateSlug } from '../lib/slug'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'


// 美食 (Food) Tab - 3 sections: Restaurants, Boba, Bloggers
export function FoodTab() {
  return (
    <div className="space-y-12">
      <RestaurantSection cuisineType="chinese" title="今天吃什么？" description="Cupertino周边最好的中餐、日本菜、韩国菜、越南菜" />
      <RestaurantSection cuisineType="boba" title="来点冰的甜的！" description="Cupertino周边最好的奶茶" />
      <BloggerSection />
    </div>
  )
}

// Restaurant Carousel Component
function RestaurantSection({ cuisineType, title, description }: { cuisineType: string, title: string, description: string }) {
  const [restaurants, setRestaurants] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchRestaurants()
  }, [cuisineType])

  const fetchRestaurants = async () => {
    setLoading(true)
    try {
      const url = `${API_URL}/food/restaurants?cuisine_type=${cuisineType}&limit=20`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setRestaurants(data.restaurants || [])
      } else {
        setRestaurants([])
      }
    } catch (error) {
      console.error('Error fetching restaurants:', error)
      setRestaurants([])
    } finally {
      setLoading(false)
    }
  }

  const handleCheckIn = async (restaurantId: number) => {
    try {
      const res = await fetch(`${API_URL}/food/checkin/${restaurantId}`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        // Update local state
        setRestaurants(prev => prev.map(r => 
          r.id === restaurantId 
            ? { ...r, check_in_count: data.check_in_count }
            : r
        ))
      }
    } catch (error) {
      console.error('Error checking in:', error)
    }
  }

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const scrollAmount = 400
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      })
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-2">{title}</h2>
        <p className="text-gray-600 mb-4">{description}</p>
        <div className="text-center py-8">加载中...</div>
      </div>
    )
  }

  if (restaurants.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-2">{title}</h2>
        <p className="text-gray-600 mb-4">{description}</p>
        <div className="text-center py-8 text-gray-500">
          暂无数据。请配置 GOOGLE_MAPS_API_KEY 以获取餐厅信息。
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-2">{title}</h2>
      <p className="text-gray-600 mb-4">{description}</p>
      
      <div className="relative">
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full shadow-lg p-2 hover:bg-gray-100"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        
        <div
          ref={scrollRef}
          className="flex gap-4 overflow-x-auto scrollbar-hide pb-4"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {restaurants.map((restaurant) => (
            <div
              key={restaurant.id}
              className="flex-shrink-0 w-80 bg-gray-50 rounded-lg overflow-hidden shadow hover:shadow-lg transition"
            >
              {restaurant.photo_url && (
                <img
                  src={restaurant.photo_url}
                  alt={restaurant.name}
                  className="w-full h-48 object-cover"
                />
              )}
              <div className="p-4">
                <h3 className="font-semibold text-lg mb-2">{restaurant.name}</h3>
                <p className="text-sm text-gray-600 mb-2">{restaurant.address}</p>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {restaurant.rating && (
                      <span className="text-yellow-500">⭐ {restaurant.rating}</span>
                    )}
                    {restaurant.user_ratings_total && (
                      <span className="text-sm text-gray-500">({restaurant.user_ratings_total})</span>
                    )}
                  </div>
                  {restaurant.is_open_now !== null && (
                    <span className={`text-xs px-2 py-1 rounded ${restaurant.is_open_now ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                      {restaurant.is_open_now ? '营业中' : '已关闭'}
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <a
                    href={restaurant.google_maps_url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(restaurant.name + ' ' + restaurant.address)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 bg-blue-500 text-white text-center py-2 px-4 rounded hover:bg-blue-600 transition"
                  >
                    查看评价
                  </a>
                  <button
                    onClick={() => handleCheckIn(restaurant.id)}
                    className="bg-gray-200 text-gray-700 py-2 px-4 rounded hover:bg-gray-300 transition flex items-center gap-2"
                  >
                    <span>打卡</span>
                    {restaurant.check_in_count > 0 && (
                      <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded">
                        {restaurant.check_in_count}
                      </span>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full shadow-lg p-2 hover:bg-gray-100"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  )
}

// Blogger Section - YouTube food blogger videos
function BloggerSection() {
  const [videos, setVideos] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/food/bloggers?limit=20`)
      if (res.ok) {
        const data = await res.json()
        setVideos(data.videos || [])
      } else {
        setVideos([])
      }
    } catch (error) {
      setVideos([])
    } finally {
      setLoading(false)
    }
  }

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const scrollAmount = 400
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      })
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-2">美食博主</h2>
        <p className="text-gray-600 mb-4">YouTube上最popular的国内美食博主最新视频</p>
        <div className="text-center py-8">加载中...</div>
      </div>
    )
  }

  if (videos.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-2">美食博主</h2>
        <p className="text-gray-600 mb-4">YouTube上最popular的国内美食博主最新视频</p>
        <div className="text-center py-8 text-gray-500">
          暂无数据。后台任务运行后会显示相关内容。
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-2">美食博主</h2>
      <p className="text-gray-600 mb-4">YouTube上最popular的国内美食博主最新视频</p>
      
      <div className="relative">
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            scroll('left')
          }}
          className="absolute left-0 top-1/2 -translate-y-1/2 z-20 bg-white rounded-full shadow-lg p-2 hover:bg-gray-100 cursor-pointer"
          type="button"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        
        <div
          ref={scrollRef}
          className="flex gap-4 overflow-x-auto scrollbar-hide pb-4 px-12"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {videos.map((video) => (
            <a
              key={video.id}
              href={video.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 w-80 bg-gray-50 rounded-lg overflow-hidden shadow hover:shadow-lg transition"
            >
              {video.thumbnail_url && (
                <img
                  src={video.thumbnail_url}
                  alt={video.title}
                  className="w-full h-48 object-cover"
                />
              )}
              <div className="p-4">
                <h3 className="font-semibold text-lg mb-2 line-clamp-2">{video.title}</h3>
                {video.summary && (
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">{video.summary}</p>
                )}
                {video.published_at && (
                  <p className="text-xs text-gray-500">
                    {new Date(video.published_at).toLocaleDateString('zh-CN')}
                  </p>
                )}
              </div>
            </a>
          ))}
        </div>
        
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            scroll('right')
          }}
          className="absolute right-0 top-1/2 -translate-y-1/2 z-20 bg-white rounded-full shadow-lg p-2 hover:bg-gray-100 cursor-pointer"
          type="button"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  )
}

// 羊毛 (Deals) Tab - Bank/credit card/brokerage/life deals
export function DealsTab() {
  const [coupons, setCoupons] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [dataFreshness, setDataFreshness] = useState<string>('fresh')
  const [usageInfo, setUsageInfo] = useState<any>(null)

  useEffect(() => {
    fetchDeals()
  }, [selectedCategory])

  const fetchDeals = async () => {
    setLoading(true)
    try {
      const url = selectedCategory 
        ? `${API_URL}/deals/feed?category=${selectedCategory}`
        : `${API_URL}/feeds/deals`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setCoupons(data.coupons || [])
        setDataFreshness(data.data_freshness || 'fresh')
        setUsageInfo(data.usage_info || null)
      } else {
        setCoupons([])
      }
    } catch (error) {
      console.error('Error fetching deals:', error)
      setCoupons([])
    } finally {
      setLoading(false)
    }
  }

  const categories = [
    { id: null, label: '全部' },
    { id: 'bank', label: '银行开户' },
    { id: 'card', label: '信用卡' },
    { id: 'brokerage', label: '证券账户' },
    { id: 'life', label: '生活羊毛' },
    { id: 'food_fast', label: '快餐 / 餐饮' },
    { id: 'retail_family', label: '日用品 / 衣服 / 鞋子' },
  ]

  if (loading) return <div className="text-center py-8">Loading deals...</div>

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">羊毛专区</h1>
        
        {/* Category Filter Tabs */}
        <div className="flex gap-2 flex-wrap">
          {categories.map((cat) => (
            <button
              key={cat.id || 'all'}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                selectedCategory === cat.id
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Data Freshness Indicator */}
        {dataFreshness === 'stale_due_to_quota' && (
          <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg p-4 text-sm text-yellow-800">
            <p className="font-medium flex items-center gap-2">
              <span>⚠️</span> 数据可能已过期
            </p>
            <p className="text-xs mt-1 text-yellow-700">由于 Google CSE API 配额限制，当前显示的是数据库中的历史数据。配额重置后将自动更新。</p>
            {usageInfo && (
              <p className="text-xs mt-2 text-yellow-700">今日使用: {usageInfo.current_usage}/{usageInfo.daily_budget}</p>
            )}
          </div>
        )}
      </div>

      {coupons.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7" />
            </svg>
          </div>
          <p className="text-lg font-medium text-gray-700 mb-2">暂无优惠信息</p>
          <p className="text-sm text-gray-500">优惠搜索任务每天自动运行，或等待配额重置后手动触发。</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {coupons.map((coupon) => (
            <div key={coupon.id} className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden flex flex-col border border-gray-100">
              {/* Media Section */}
              {coupon.video_url && (
                <div className="w-full relative" style={{ paddingBottom: '56.25%' }}>
                  {coupon.video_url.includes('youtube.com') || coupon.video_url.includes('youtu.be') ? (
                    (() => {
                      const videoId = coupon.video_url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/)?.[1];
                      const embedUrl = videoId ? `https://www.youtube.com/embed/${videoId}?rel=0` : null;
                      return embedUrl ? (
                        <iframe
                          src={embedUrl}
                          title={coupon.title || 'Video'}
                          frameBorder="0"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                          allowFullScreen
                          className="absolute inset-0 w-full h-full"
                        />
                      ) : (
                        <a href={coupon.video_url} target="_blank" rel="noopener noreferrer" className="absolute inset-0 bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition">
                          <span className="text-gray-600">点击观看视频</span>
                        </a>
                      );
                    })()
                  ) : (
                    <video
                      src={coupon.video_url}
                      controls
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  )}
                </div>
              )}
              {!coupon.video_url && coupon.image_url && (
                <div className="w-full h-48 overflow-hidden bg-gray-100">
                  <img
                    src={coupon.image_url}
                    alt={coupon.title || 'Coupon image'}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
              )}
              
              {/* Content Section */}
              <div className="p-5 flex-1 flex flex-col">
                <h3 className="text-lg font-semibold mb-3 text-gray-900 line-clamp-2 leading-snug">{coupon.title}</h3>
                
                {coupon.code && (
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-3 mb-3">
                    <p className="text-xs text-gray-600 mb-1 font-medium">优惠码</p>
                    <p className="text-blue-600 font-bold text-xl tracking-wider">{coupon.code}</p>
                  </div>
                )}
                
                {/* Tags */}
                <div className="flex gap-2 flex-wrap mb-3">
                  {coupon.category && (
                    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {coupon.category === 'bank' ? '银行开户' :
                       coupon.category === 'card' ? '信用卡' :
                       coupon.category === 'brokerage' ? '证券账户' :
                       coupon.category === 'life' ? '生活羊毛' :
                       coupon.category === 'food_fast' ? '快餐 / 餐饮' :
                       coupon.category === 'retail_family' ? '日用品 / 衣服 / 鞋子' :
                       coupon.category}
                    </span>
                  )}
                  {coupon.chinese_friendliness_score && coupon.chinese_friendliness_score > 0.6 && (
                    <span 
                      className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                      title="老中友好：操作简单 / 风险低"
                    >
                      ✓ 老中友好
                    </span>
                  )}
                </div>
                
                {coupon.city && (
                  <p className="text-sm text-gray-500 mb-2 flex items-center gap-1">
                    <span>📍</span> {coupon.city}
                  </p>
                )}
                
                {coupon.terms && (
                  <p className="text-sm text-gray-600 mb-4 flex-1 line-clamp-3 leading-relaxed">{coupon.terms}</p>
                )}
                
                {/* Footer */}
                <div className="mt-auto pt-3 border-t border-gray-100">
                  <div className="flex items-center justify-between">
                    {coupon.source && (
                      <span className="text-xs text-gray-500">{coupon.source}</span>
                    )}
                    {coupon.source_url && (
                      <a
                        href={coupon.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
                      >
                        查看详情
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Holding Actions Component
function HoldingActions({ ticker, currentQuantity, onAdd, onReduce, onReload }: {
  ticker: string
  currentQuantity: number
  onAdd: (ticker: string, quantity: number, costBasisPerShare: number) => Promise<void>
  onReduce: (ticker: string, quantity: number) => Promise<void>
  onReload: () => Promise<void>
}) {
  const [showAddForm, setShowAddForm] = useState(false)
  const [showReduceForm, setShowReduceForm] = useState(false)
  const [addQuantity, setAddQuantity] = useState('')
  const [addCostBasis, setAddCostBasis] = useState('')
  const [reduceQuantity, setReduceQuantity] = useState('')

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const qty = parseFloat(addQuantity)
    const cost = parseFloat(addCostBasis)
    if (qty > 0 && cost > 0) {
      await onAdd(ticker, qty, cost)
      setAddQuantity('')
      setAddCostBasis('')
      setShowAddForm(false)
    }
  }

  const handleReduceSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const qty = parseFloat(reduceQuantity)
    if (qty > 0 && qty <= currentQuantity) {
      await onReduce(ticker, qty)
      setReduceQuantity('')
      setShowReduceForm(false)
    } else {
      alert(`Quantity must be between 0 and ${currentQuantity}`)
    }
  }

  return (
    <div className="flex items-center space-x-2">
      {!showAddForm && !showReduceForm ? (
        <>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200"
          >
            + 加仓
          </button>
          <button
            onClick={() => setShowReduceForm(true)}
            className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            - 减仓
          </button>
        </>
      ) : showAddForm ? (
        <form onSubmit={handleAddSubmit} className="flex items-center space-x-1">
          <input
            type="number"
            step="0.01"
            placeholder="数量"
            value={addQuantity}
            onChange={(e) => setAddQuantity(e.target.value)}
            className="w-16 px-1 py-0.5 text-xs border rounded"
            required
          />
          <input
            type="number"
            step="0.01"
            placeholder="成本/股"
            value={addCostBasis}
            onChange={(e) => setAddCostBasis(e.target.value)}
            className="w-20 px-1 py-0.5 text-xs border rounded"
            required
          />
          <button
            type="submit"
            className="px-2 py-0.5 text-xs bg-green-600 text-white rounded hover:bg-green-700"
          >
            确认
          </button>
          <button
            type="button"
            onClick={() => {
              setShowAddForm(false)
              setAddQuantity('')
              setAddCostBasis('')
            }}
            className="px-2 py-0.5 text-xs bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            取消
          </button>
        </form>
      ) : (
        <form onSubmit={handleReduceSubmit} className="flex items-center space-x-1">
          <input
            type="number"
            step="0.01"
            placeholder="数量"
            value={reduceQuantity}
            onChange={(e) => setReduceQuantity(e.target.value)}
            className="w-16 px-1 py-0.5 text-xs border rounded"
            required
            max={currentQuantity}
          />
          <button
            type="submit"
            className="px-2 py-0.5 text-xs bg-red-600 text-white rounded hover:bg-red-700"
          >
            确认
          </button>
          <button
            type="button"
            onClick={() => {
              setShowReduceForm(false)
              setReduceQuantity('')
            }}
            className="px-2 py-0.5 text-xs bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
          >
            取消
          </button>
        </form>
      )}
    </div>
  )
}

// 暴富 (Wealth) Tab - YouTube stock investment videos in carousel
export function WealthTab() {
  const [videos, setVideos] = useState<any[]>([])
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [portfolioLoading, setPortfolioLoading] = useState(true)
  const [sortColumn, setSortColumn] = useState<string | null>('value')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [intradayDataCache, setIntradayDataCache] = useState<Record<string, any[]>>({})
  const [investmentAdvice, setInvestmentAdvice] = useState<string | null>(null)
  const [adviceLoading, setAdviceLoading] = useState(false)
  const [highOffers, setHighOffers] = useState<any[]>([])
  const [offersLoading, setOffersLoading] = useState(true)
  const [marketSnapshot, setMarketSnapshot] = useState<any>(null)
  const [marketLoading, setMarketLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const videoCarouselRef = useRef<HTMLDivElement>(null)
  const offersCarouselRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchWealth()
    loadPortfolio()
    fetchHighOffers()
    fetchMarketSnapshot()
  }, [])

  useEffect(() => {
    // Load investment advice after portfolio is loaded
    if (portfolioData && portfolioData.holdings && portfolioData.holdings.length > 0) {
      loadInvestmentAdvice()
    }
  }, [portfolioData])

  const fetchWealth = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/feeds/wealth`)
      if (res.ok) {
        const data = await res.json()
        setVideos(data.articles || [])
      } else {
        setVideos([])
      }
    } catch (error) {
      console.error('Error fetching wealth feed:', error)
      setVideos([])
    } finally {
      setLoading(false)
    }
  }

  const loadPortfolio = async () => {
    setPortfolioLoading(true)
    try {
      const res = await fetch(`${API_URL}/portfolio/db-summary`)
      if (res.ok) {
        const data = await res.json()
        setPortfolioData(data)
        
        // Load intraday data lazily in background (after initial render)
        setTimeout(() => {
          loadIntradayDataLazily(data.holdings || [])
        }, 1000)
      } else {
        console.error('Error loading portfolio:', res.status, res.statusText)
      }
    } catch (error) {
      console.error('Error loading portfolio:', error)
    } finally {
      setPortfolioLoading(false)
    }
  }

  const loadInvestmentAdvice = async () => {
    setAdviceLoading(true)
    try {
      const res = await fetch(`${API_URL}/portfolio/advice`)
      if (res.ok) {
        const data = await res.json()
        setInvestmentAdvice(data.advice || null)
      } else {
        console.error('Error loading investment advice:', res.status, res.statusText)
      }
    } catch (error) {
      console.error('Error loading investment advice:', error)
    } finally {
      setAdviceLoading(false)
    }
  }

  const loadIntradayDataLazily = async (holdings: any[]) => {
    // Load intraday data in batches to avoid overwhelming the API
    const loadBatch = async (batch: any[]) => {
      for (const holding of batch) {
        try {
          const res = await fetch(`${API_URL}/portfolio/intraday/${holding.ticker}`)
          if (res.ok) {
            const data = await res.json()
            if (data.intraday_data && data.intraday_data.length > 0) {
              setIntradayDataCache(prev => ({
                ...prev,
                [holding.ticker]: data.intraday_data
              }))
            }
          }
          // Small delay between requests
          await new Promise(resolve => setTimeout(resolve, 200))
        } catch (error) {
        }
      }
    }
    
    // Load in batches of 3 to avoid rate limits
    const batchSize = 3
    for (let i = 0; i < holdings.length; i += batchSize) {
      const batch = holdings.slice(i, i + batchSize)
      await loadBatch(batch)
    }
  }

  const handleAddPosition = async (ticker: string, quantity: number, costBasisPerShare: number) => {
    try {
      const res = await fetch(`${API_URL}/portfolio/add-position`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ticker: ticker,
          quantity: quantity,
          cost_basis_per_share: costBasisPerShare
        })
      })
      if (res.ok) {
        await loadPortfolio() // Reload portfolio
      } else {
        const error = await res.json()
        alert(`Error: ${error.detail || 'Failed to add position'}`)
      }
    } catch (error) {
      console.error('Error adding position:', error)
      alert('Failed to add position')
    }
  }

  const handleReducePosition = async (ticker: string, quantity: number) => {
    try {
      const res = await fetch(`${API_URL}/portfolio/reduce-position`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ticker: ticker,
          quantity: quantity
        })
      })
      if (res.ok) {
        await loadPortfolio() // Reload portfolio
      } else {
        const error = await res.json()
        alert(`Error: ${error.detail || 'Failed to reduce position'}`)
      }
    } catch (error) {
      console.error('Error reducing position:', error)
      alert('Failed to reduce position')
    }
  }

  const getGoogleFinanceUrl = (ticker: string) => {
    // Google Finance URL format
    // Try with NASDAQ first, Google will redirect if needed
    return `https://www.google.com/finance/quote/${ticker}:NASDAQ`
  }

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      // Toggle direction if clicking the same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      // Set new column and default to descending
      setSortColumn(column)
      setSortDirection('desc')
    }
  }

  const getSortedHoldings = () => {
    if (!portfolioData || !portfolioData.holdings || !sortColumn) {
      return portfolioData?.holdings || []
    }

    const holdings = [...portfolioData.holdings]
    holdings.sort((a: any, b: any) => {
      let aValue: any
      let bValue: any

      switch (sortColumn) {
        case 'ticker':
          aValue = a.ticker
          bValue = b.ticker
          break
        case 'price':
          aValue = a.current_price || 0
          bValue = b.current_price || 0
          break
        case 'quantity':
          aValue = a.quantity
          bValue = b.quantity
          break
        case 'day_gain':
          aValue = a.day_gain !== null && a.day_gain !== undefined ? a.day_gain : -Infinity
          bValue = b.day_gain !== null && b.day_gain !== undefined ? b.day_gain : -Infinity
          break
        case 'total_gain':
          aValue = a.total_gain
          bValue = b.total_gain
          break
        case 'value':
          aValue = a.value
          bValue = b.value
          break
        default:
          return 0
      }

      // Handle string comparison
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue)
      }

      // Handle numeric comparison
      if (sortDirection === 'asc') {
        return aValue - bValue
      } else {
        return bValue - aValue
      }
    })

    return holdings
  }

  const getSortIcon = (column: string) => {
    if (sortColumn !== column) {
      return (
        <span className="ml-1 text-gray-400">
          <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
        </span>
      )
    }
    return sortDirection === 'asc' ? (
      <span className="ml-1 text-blue-600">
        <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
      </span>
    ) : (
      <span className="ml-1 text-blue-600">
        <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </span>
    )
  }

  const renderIntradayChart = (holding: any, intradayData: any[] | null = null) => {
    const data = intradayData !== null ? intradayData : (holding.intraday_data || [])
    if (!data || data.length === 0) {
      return (
        <div className="w-20 h-10 flex items-center justify-center text-gray-400 text-xs">
          N/A
        </div>
      )
    }

    const width = 80
    const height = 40
    const padding = 4
    
    // Extract prices
    const prices = data.map((d: any) => d.price)
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)
    const priceRange = maxPrice - minPrice || 1
    
    // Calculate if overall trend is up or down
    const firstPrice = prices[0]
    const lastPrice = prices[prices.length - 1]
    const isPositive = lastPrice >= firstPrice
    const color = isPositive ? '#10b981' : '#ef4444' // green or red
    
    // Normalize prices to chart coordinates
    const points = prices.map((price: number, index: number) => {
      const x = padding + (index / (prices.length - 1)) * (width - 2 * padding)
      const y = height - padding - ((price - minPrice) / priceRange) * (height - 2 * padding)
      return `${x},${y}`
    }).join(' ')
    
    // Create area fill path
    const areaPath = `M ${padding},${height - padding} L ${points.split(' ').map((p: string, i: number) => {
      if (i === 0) return p.split(',')[0]
      return p
    }).join(' L ')} L ${width - padding},${height - padding} Z`
    
    return (
      <div className="w-20 h-10">
        <svg width={width} height={height} className="overflow-visible">
          {/* Area fill */}
          <path
            d={areaPath}
            fill={color}
            fillOpacity="0.2"
          />
          {/* Line */}
          <polyline
            points={points}
            fill="none"
            stroke={color}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    )
  }

  const scrollCarousel = (direction: 'left' | 'right', ref: React.RefObject<HTMLDivElement>) => {
    if (ref.current) {
      const scrollAmount = 400
      const currentScroll = ref.current.scrollLeft
      const newScroll = direction === 'left' ? currentScroll - scrollAmount : currentScroll + scrollAmount
      ref.current.scrollLeft = newScroll
    }
  }

  const fetchHighOffers = async () => {
    setOffersLoading(true)
    try {
      const res = await fetch(`${API_URL}/wealth/offers?limit=20`)
      if (res.ok) {
        const data = await res.json()
        setHighOffers(data.articles || [])
      } else {
        setHighOffers([])
      }
    } catch (error) {
      console.error('Error fetching high offers:', error)
      setHighOffers([])
    } finally {
      setOffersLoading(false)
    }
  }

  const fetchMarketSnapshot = async () => {
    setMarketLoading(true)
    try {
      const res = await fetch(`${API_URL}/market/snapshot`)
      if (res.ok) {
        const data = await res.json()
        setMarketSnapshot(data)
      }
    } catch (error) {
      console.error('Error fetching market snapshot:', error)
    } finally {
      setMarketLoading(false)
    }
  }

  // Helper function to format Powerball jackpot
  const formatPowerballJackpot = (amount: number): string => {
    if (amount >= 1_000_000_000) {
      return `$${(amount / 1_000_000_000).toFixed(1)}B`
    } else {
      return `$${(amount / 1_000_000).toFixed(0)}M`
    }
  }

  // Show loading only if both are loading
  if (loading && portfolioLoading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="space-y-8">
      {/* Top Banner: Gold, Powerball, BTC, Jumbo Loan, T-bill */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-lg shadow-lg p-4">
        <div className="flex items-center justify-around text-white flex-wrap gap-4">
          {/* Gold Price */}
          <div className="flex items-center space-x-3">
            <div className="text-yellow-400">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <div className="text-xs text-gray-400">黄金</div>
              {marketLoading ? (
                <div className="text-sm text-gray-500">加载中...</div>
              ) : marketSnapshot ? (
                <div className="text-lg font-bold text-yellow-400">
                  ${(marketSnapshot.gold_usd_per_oz || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              ) : (
                <div className="text-sm text-gray-500">N/A</div>
              )}
            </div>
          </div>

          {/* Divider */}
          <div className="h-12 w-px bg-gray-600"></div>

          {/* Powerball */}
          <div className="flex items-center space-x-3">
            <div className="text-red-400">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <div className="text-xs text-gray-400">Powerball</div>
              {marketLoading ? (
                <div className="text-sm text-gray-500">加载中...</div>
              ) : marketSnapshot ? (
                <div className="text-lg font-bold text-red-400">
                  {formatPowerballJackpot(marketSnapshot.powerball_jackpot_usd || 0)}
                </div>
              ) : (
                <div className="text-sm text-gray-500">N/A</div>
              )}
            </div>
          </div>

          {/* Divider */}
          <div className="h-12 w-px bg-gray-600"></div>

          {/* BTC Price */}
          <div className="flex items-center space-x-3">
            <div className="text-orange-400">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <div className="text-xs text-gray-400">BTC</div>
              {marketLoading ? (
                <div className="text-sm text-gray-500">加载中...</div>
              ) : marketSnapshot ? (
                <div className="text-lg font-bold text-orange-400">
                  ${(marketSnapshot.btc_usd || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                </div>
              ) : (
                <div className="text-sm text-gray-500">N/A</div>
              )}
            </div>
          </div>

          {/* Divider */}
          <div className="h-12 w-px bg-gray-600"></div>

          {/* Jumbo Loan 7/1 ARM */}
          <div className="flex items-center space-x-3">
            <div className="text-blue-400">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                <path fillRule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <div className="text-xs text-gray-400">CA Jumbo 7/1 ARM</div>
              {marketLoading ? (
                <div className="text-sm text-gray-500">加载中...</div>
              ) : marketSnapshot ? (
                <div className="text-lg font-bold text-blue-400">
                  {(marketSnapshot.ca_jumbo_7_1_arm_rate || 0).toFixed(2)}%
                </div>
              ) : (
                <div className="text-sm text-gray-500">N/A</div>
              )}
            </div>
          </div>

          {/* Divider */}
          <div className="h-12 w-px bg-gray-600"></div>

          {/* T-bill Rate */}
          <div className="flex items-center space-x-3">
            <div className="text-green-400">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4zm6 4a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <div className="text-xs text-gray-400">T-bill 3-month</div>
              {marketLoading ? (
                <div className="text-sm text-gray-500">加载中...</div>
              ) : marketSnapshot ? (
                <div className="text-lg font-bold text-green-400">
                  {(marketSnapshot.t_bill_3m_rate || 0).toFixed(2)}%
                </div>
              ) : (
                <div className="text-sm text-gray-500">N/A</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Portfolio Summary Section - Google Finance Style */}
      {portfolioData && Array.isArray(portfolioData.holdings) && portfolioData.holdings.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          {/* Portfolio Header */}
          <div className="mb-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h2 className="text-2xl font-bold mb-2">股票持仓</h2>
                <div className="flex items-baseline space-x-4">
                  <div>
                    <div className="text-3xl font-bold text-gray-900">
                      ${portfolioData.total_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {new Date().toLocaleString('zh-CN', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })} UTC-8 USD
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {portfolioData.day_gain >= 0 ? (
                      <span className="text-green-600 font-semibold">↑{Math.abs(portfolioData.day_gain_percent).toFixed(2)}%</span>
                    ) : (
                      <span className="text-red-600 font-semibold">↓{Math.abs(portfolioData.day_gain_percent).toFixed(2)}%</span>
                    )}
                    <span className={portfolioData.day_gain >= 0 ? "text-green-600" : "text-red-600"}>
                      {portfolioData.day_gain >= 0 ? '+' : ''}${Math.abs(portfolioData.day_gain).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Today
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Portfolio Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Day Gain</div>
              <div className={portfolioData.day_gain >= 0 ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
                {portfolioData.day_gain >= 0 ? '+' : ''}${Math.abs(portfolioData.day_gain).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className={portfolioData.day_gain_percent >= 0 ? "text-green-600 text-sm" : "text-red-600 text-sm"}>
                ({portfolioData.day_gain_percent >= 0 ? '↑' : '↓'}{Math.abs(portfolioData.day_gain_percent).toFixed(2)}%)
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Total Gain</div>
              <div className={portfolioData.total_pnl >= 0 ? "text-green-600 font-semibold" : "text-red-600 font-semibold"}>
                {portfolioData.total_pnl >= 0 ? '+' : ''}${Math.abs(portfolioData.total_pnl).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
              <div className={portfolioData.total_pnl_percent >= 0 ? "text-green-600 text-sm" : "text-red-600 text-sm"}>
                ({portfolioData.total_pnl_percent >= 0 ? '↑' : '↓'}{Math.abs(portfolioData.total_pnl_percent).toFixed(2)}%)
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600 mb-1">Total Cost</div>
              <div className="text-gray-900 font-semibold">
                ${portfolioData.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {/* Holdings Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th 
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('ticker')}
                  >
                    <div className="flex items-center">
                      SYMBOL
                      {getSortIcon('ticker')}
                    </div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    CHART
                  </th>
                  <th 
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('price')}
                  >
                    <div className="flex items-center">
                      PRICE
                      {getSortIcon('price')}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('quantity')}
                  >
                    <div className="flex items-center">
                      QUANTITY
                      {getSortIcon('quantity')}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('day_gain')}
                  >
                    <div className="flex items-center">
                      DAY GAIN
                      {getSortIcon('day_gain')}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('total_gain')}
                  >
                    <div className="flex items-center">
                      TOTAL GAIN
                      {getSortIcon('total_gain')}
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('value')}
                  >
                    <div className="flex items-center">
                      VALUE
                      {getSortIcon('value')}
                    </div>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ACTIONS
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(() => {
                  const sortedHoldings = getSortedHoldings()
                  const totalHoldings = sortedHoldings.length
                  const itemsPerPage = Math.ceil(totalHoldings / 2) // 分为两页
                  const startIndex = (currentPage - 1) * itemsPerPage
                  const endIndex = startIndex + itemsPerPage
                  const currentHoldings = sortedHoldings.slice(startIndex, endIndex)
                  
                  return currentHoldings.map((holding: any, index: number) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <a
                        href={getGoogleFinanceUrl(holding.ticker)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {holding.ticker}
                      </a>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {renderIntradayChart(holding, intradayDataCache[holding.ticker] || null)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {holding.current_price ? `$${holding.current_price.toFixed(2)}` : 'N/A'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {holding.quantity.toLocaleString(undefined, { maximumFractionDigits: 3 })}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {holding.day_gain !== null && holding.day_gain !== undefined ? (
                        <span className={holding.day_gain >= 0 ? "text-green-600" : "text-red-600"}>
                          {holding.day_gain >= 0 ? '+' : ''}${Math.abs(holding.day_gain).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          {' '}
                          ({holding.day_gain_percent >= 0 ? '↑' : '↓'}{Math.abs(holding.day_gain_percent).toFixed(2)}%)
                        </span>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <span className={holding.total_gain >= 0 ? "text-green-600" : "text-red-600"}>
                        {holding.total_gain >= 0 ? '+' : ''}${Math.abs(holding.total_gain).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        {' '}
                        ({holding.total_gain_percent >= 0 ? '↑' : '↓'}{Math.abs(holding.total_gain_percent).toFixed(2)}%)
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 font-medium">
                      ${holding.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <HoldingActions 
                        ticker={holding.ticker}
                        currentQuantity={holding.quantity}
                        onAdd={handleAddPosition}
                        onReduce={handleReducePosition}
                        onReload={loadPortfolio}
                      />
                    </td>
                  </tr>
                  ))
                })()}
              </tbody>
            </table>
          </div>
          
          {/* Pagination Controls */}
          {(() => {
            const sortedHoldings = getSortedHoldings()
            const totalHoldings = sortedHoldings.length
            const totalPages = 2 // 固定两页
            const itemsPerPage = Math.ceil(totalHoldings / totalPages)
            
            if (totalHoldings <= itemsPerPage) {
              return null // 如果股票数量少于一页，不显示分页
            }
            
            return (
              <div className="mt-4 flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
                <div className="flex flex-1 justify-between sm:hidden">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    上一页
                  </button>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    下一页
                  </button>
                </div>
                <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      显示 <span className="font-medium">{((currentPage - 1) * itemsPerPage) + 1}</span> 到{' '}
                      <span className="font-medium">{Math.min(currentPage * itemsPerPage, totalHoldings)}</span> 条，共{' '}
                      <span className="font-medium">{totalHoldings}</span> 条
                    </p>
                  </div>
                  <div>
                    <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span className="sr-only">上一页</span>
                        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                          <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                        </svg>
                      </button>
                      {[1, 2].map((page) => (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                            currentPage === page
                              ? 'z-10 bg-blue-600 text-white focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                              : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                      <button
                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                        className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span className="sr-only">下一页</span>
                        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                          <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                        </svg>
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )
          })()}

          {/* Gemini Investment Advice Section */}
          {portfolioData && portfolioData.holdings && portfolioData.holdings.length > 0 && (
            <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900 flex items-center">
                  <svg className="w-6 h-6 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Gemini 投资建议
                </h3>
                {adviceLoading && (
                  <div className="text-sm text-gray-500">生成中...</div>
                )}
              </div>
              
              {adviceLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">正在分析您的投资组合...</span>
                </div>
              ) : investmentAdvice ? (
                <div className="prose max-w-none">
                  <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {investmentAdvice.split('\n').map((line: string, idx: number) => {
                      // Format bold text (lines starting with **)
                      if (line.trim().startsWith('**') && line.trim().endsWith('**')) {
                        const text = line.trim().replace(/\*\*/g, '')
                        return (
                          <div key={idx} className="font-bold text-gray-900 mt-4 mb-2 text-lg">
                            {text}
                          </div>
                        )
                      } else if (line.trim().startsWith('**')) {
                        const text = line.replace(/\*\*/g, '')
                        return (
                          <div key={idx} className="font-semibold text-gray-900 mt-3 mb-1">
                            {text}
                          </div>
                        )
                      } else if (line.trim().startsWith('-') || line.trim().startsWith('•')) {
                        return (
                          <div key={idx} className="ml-4 mb-2 text-gray-700">
                            {line}
                          </div>
                        )
                      } else if (line.trim() === '') {
                        return <div key={idx} className="mb-2"></div>
                      } else {
                        return (
                          <div key={idx} className="mb-2 text-gray-700">
                            {line}
                          </div>
                        )
                      }
                    })}
                  </div>
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500">
                  <p className="mb-2">无法获取投资建议。</p>
                  <p className="text-sm">请确保已配置 GEMINI_API_KEY 环境变量，并且 API 密钥有效。</p>
                  <p className="text-xs mt-2 text-gray-400">
                    配置方法：在项目根目录的 .env 文件中添加 GEMINI_API_KEY=your_api_key_here
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Video Carousel Section */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">热门投资视频</h2>
        {videos.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            暂无内容。后台任务运行后会显示美股投资视频。
          </div>
        ) : (
          <div className="relative">
            {/* Left scroll button */}
            <button
              onClick={() => scrollCarousel('left', videoCarouselRef)}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition"
              style={{ marginLeft: '-20px' }}
            >
              <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            {/* Right scroll button */}
            <button
              onClick={() => scrollCarousel('right', videoCarouselRef)}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition"
              style={{ marginRight: '-20px' }}
            >
              <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>

            <div 
              ref={videoCarouselRef}
              className="overflow-x-auto pb-4" 
              style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}
            >
              <div className="flex space-x-4" style={{ minWidth: 'max-content' }}>
                {videos.map((video) => (
                  <div
                    key={video.id}
                    className="flex-shrink-0 w-96 bg-white rounded-lg shadow hover:shadow-lg transition overflow-hidden"
                  >
                    {video.video_id ? (
                      <div 
                        className="rounded-t-lg overflow-hidden" 
                        style={{ 
                          position: 'relative', 
                          paddingBottom: '56.25%', 
                          height: 0, 
                          backgroundColor: '#000'
                        }}
                      >
                        <iframe
                          src={`https://www.youtube.com/embed/${video.video_id}?rel=0`}
                          title={video.title || 'YouTube video'}
                          frameBorder="0"
                          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                          allowFullScreen
                          style={{ 
                            position: 'absolute', 
                            top: 0, 
                            left: 0, 
                            width: '100%', 
                            height: '100%',
                            border: 'none'
                          }}
                        />
                      </div>
                    ) : video.thumbnail_url ? (
                      <div className="w-full h-48 overflow-hidden">
                        <img
                          src={video.thumbnail_url}
                          alt={video.title || 'Video thumbnail'}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    ) : null}
                    <a
                      href={video.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-4"
                    >
                      <h3 className="text-sm font-semibold hover:text-blue-600 line-clamp-2 mb-2">{video.title}</h3>
                      {video.published_at && (
                        <p className="text-xs text-gray-500">
                          {new Date(video.published_at).toLocaleDateString('zh-CN')}
                        </p>
                      )}
                    </a>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Latest Packages Carousel Section */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2">📦 最新包裹</h2>
        <p className="text-sm text-gray-600 mb-4">1亩三分地最近3天最火的包裹offer帖</p>
        {offersLoading ? (
          <div className="text-center py-8 text-gray-500">加载中...</div>
        ) : highOffers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            暂无内容。后台任务运行后会显示最新包裹帖子。
          </div>
        ) : (
          <div className="relative">
            <button
              onClick={() => scrollCarousel('left', offersCarouselRef)}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition"
              style={{ marginLeft: '-20px' }}
            >
              <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={() => scrollCarousel('right', offersCarouselRef)}
              className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition"
              style={{ marginRight: '-20px' }}
            >
              <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <div 
              ref={offersCarouselRef}
              className="overflow-x-auto pb-4" 
              style={{ scrollbarWidth: 'none', msOverflowStyle: 'none', WebkitOverflowScrolling: 'touch' }}
            >
              <div className="flex space-x-4" style={{ minWidth: 'max-content' }}>
                {highOffers.map((offer) => (
                  <a
                    key={offer.id}
                    href={offer.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 w-96 bg-white rounded-xl shadow-sm hover:shadow-md transition overflow-hidden border border-gray-100"
                  >
                    <div className="p-5">
                      <h3 className="text-base font-semibold hover:text-blue-600 line-clamp-2 mb-2 text-gray-900">{offer.title}</h3>
                      {offer.summary && (
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{offer.summary}</p>
                      )}
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center gap-3">
                          <span>1point3acres</span>
                          {(offer.views || 0) > 0 && (
                            <span className="flex items-center gap-1">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              {offer.views}
                            </span>
                          )}
                          {(offer.saves || 0) > 0 && (
                            <span className="flex items-center gap-1">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                              </svg>
                              {offer.saves}
                            </span>
                          )}
                        </div>
                        {offer.published_at && (
                          <span>{new Date(offer.published_at).toLocaleDateString('zh-CN')}</span>
                        )}
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// 八卦 (Gossip) Tab - Trending posts from 1point3acres and Teamblind
export function GossipTab() {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchGossip()
  }, [])

  const fetchGossip = async () => {
    setLoading(true)
    try {
      const url = `${API_URL}/feeds/gossip`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setArticles(data.articles || [])
      } else {
        setArticles([])
      }
    } catch (error) {
      console.error('Error fetching gossip:', error)
      setArticles([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-8">加载中...</div>

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">八卦专区</h1>
        <p className="text-gray-600">来自 1point3acres 和 Teamblind 的热门帖子</p>
      </div>

      {articles.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <p className="text-lg font-medium text-gray-700 mb-2">暂无内容</p>
          <p className="text-sm text-gray-500">后台任务运行后会显示热门帖子。</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {articles.map((article) => (
            <Link
              key={article.id}
              href={`/posts/${article.source_type === 'di_li' ? '1point3acres' : article.source_type === 'reddit' ? 'reddit' : 'teamblind'}/${generateSlug(article.title || '')}-${article.id}`}
              className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 p-6 border border-gray-100 block"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold flex-1 text-gray-900 line-clamp-2 leading-snug pr-4">{article.title}</h3>
                <span className="flex-shrink-0 px-3 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                  {article.source_type === 'di_li' ? '1point3acres' : article.source_type === 'reddit' ? 'Reddit' : 'Teamblind'}
                </span>
              </div>
              {article.summary && (
                <p className="text-gray-600 mb-3 line-clamp-2 leading-relaxed">{article.summary}</p>
              )}
              {/* Gossip tags */}
              {article.tags && (() => {
                try {
                  const tags = JSON.parse(article.tags);
                  const gossipTags = ['职场瓜', '家庭瓜', '身份瓜', '感情瓜'];
                  const filteredTags = Array.isArray(tags) ? tags.filter(t => gossipTags.includes(t)) : [];
                  if (filteredTags.length > 0) {
                    return (
                      <div className="flex gap-2 mb-3">
                        {filteredTags.map((tag, idx) => (
                          <span key={idx} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            {tag}
                          </span>
                        ))}
                      </div>
                    );
                  }
                } catch {}
                return null;
              })()}
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  {article.gossip_score && article.gossip_score > 0 && (
                    <span className="flex items-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      八卦度: {(article.gossip_score * 100).toFixed(0)}%
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    热度: {article.final_score.toFixed(2)}
                  </span>
                  {article.city_hints && (
                    <span className="flex items-center gap-1">
                      <span>📍</span>
                      {(() => {
                        try {
                          const cities = JSON.parse(article.city_hints);
                          return Array.isArray(cities) && cities.length > 0 ? cities[0] : '';
                        } catch {
                          return '';
                        }
                      })()}
                    </span>
                  )}
                </div>
                <span className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                  查看详情 →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

