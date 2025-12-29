'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  console.log('[Home] Component rendering, activeTab:', 'wealth')
  const [activeTab, setActiveTab] = useState<'food' | 'deals' | 'wealth' | 'gossip'>('wealth')

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">湾区牛马日常</h1>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {([
              { key: 'wealth', label: '暴富' },
              { key: 'food', label: '美食' },
              { key: 'deals', label: '羊毛' },
              { key: 'gossip', label: '八卦' }
            ] as const).map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-8">
          {activeTab === 'wealth' && <WealthTab />}
          {activeTab === 'food' && <FoodTab />}
          {activeTab === 'deals' && <DealsTab />}
          {activeTab === 'gossip' && <GossipTab />}
        </div>
      </div>
    </div>
  )
}


// 美食 (Food) Tab - Food content from YouTube, Instagram, TikTok
function FoodTab() {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchFood()
  }, [])

  const fetchFood = async () => {
    console.log('[Food Feed] Starting fetch...', API_URL)
    setLoading(true)
    try {
      const url = `${API_URL}/feeds/food`
      console.log('[Food Feed] Fetching from:', url)
      const res = await fetch(url)
      console.log('[Food Feed] Response status:', res.status, res.statusText)
      
      if (res.ok) {
        const data = await res.json()
        console.log('[Food Feed] Data received:', {
          total: data.total,
          articlesCount: data.articles?.length || 0
        })
        
        const articles = data.articles || []
        setArticles(articles)
      } else {
        setArticles([])
      }
    } catch (error) {
      setArticles([])
    } finally {
      setLoading(false)
    }
  }

  console.log('[Food Tab] Render - loading:', loading, 'articles:', articles.length)
  
  if (loading) {
    console.log('[Food Tab] Showing loading state')
    return <div className="text-center py-8">Loading food content...</div>
  }

  const getPlatformBadgeColor = (platform: string) => {
    switch (platform) {
      case 'youtube': return 'bg-red-100 text-red-800'
      case 'tiktok': return 'bg-black text-white'
      case 'instagram': return 'bg-pink-100 text-pink-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const renderMedia = (article: any) => {
    // YouTube video embed
    if (article.platform === 'youtube' && article.video_id) {
      const embedUrl = `https://www.youtube.com/embed/${article.video_id}?rel=0`
      console.log('[renderMedia] Rendering YouTube video:', {
        articleId: article.id,
        video_id: article.video_id,
        embedUrl,
        title: article.title?.substring(0, 30)
      })
      return (
        <div 
          className="mb-4 rounded-lg overflow-hidden" 
          style={{ 
            position: 'relative', 
            paddingBottom: '56.25%', 
            height: 0, 
            backgroundColor: '#000',
            minHeight: '315px'
          }}
        >
          <iframe
            src={embedUrl}
            title={article.title || 'YouTube video'}
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
      )
    }
    
    // Thumbnail image (for YouTube without video_id, or other platforms)
    if (article.thumbnail_url) {
      return (
        <div className="w-full rounded-t-lg overflow-hidden">
          <img
            src={article.thumbnail_url}
            alt={article.title || 'Content thumbnail'}
            className="w-full h-48 object-cover"
            onError={(e) => {
              // Hide image if it fails to load
              e.currentTarget.style.display = 'none'
            }}
          />
        </div>
      )
    }
    
    // For YouTube channel/playlist URLs without video_id, show a placeholder
    if (article.platform === 'youtube' && !article.video_id) {
      return (
        <div className="w-full rounded-t-lg overflow-hidden bg-gray-200 aspect-video flex items-center justify-center">
          <div className="text-center text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-2" fill="currentColor" viewBox="0 0 24 24">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
            </svg>
            <p className="text-sm">YouTube Channel/Playlist</p>
            <p className="text-xs mt-1">Click to view</p>
          </div>
        </div>
      )
    }
    
    return null
  }

  return (
    <div className="space-y-4">
      {articles.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          暂无内容。后台任务运行后会显示美食探索内容。
        </div>
      ) : (
        <div 
          style={{ 
            display: 'grid !important', 
            gridTemplateColumns: 'repeat(2, 1fr) !important',
            gap: '1.5rem',
            width: '100%'
          }}
          className="food-grid"
        >
          {articles.map((article) => (
            <div
              key={article.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition overflow-hidden flex flex-col"
            >
              {renderMedia(article)}
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-6 flex-1 flex flex-col"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold flex-1 hover:text-blue-600 line-clamp-2">{article.title}</h3>
                  {article.platform && (
                    <span className={`ml-2 px-2 py-1 text-xs font-medium rounded flex-shrink-0 ${getPlatformBadgeColor(article.platform)}`}>
                      {article.platform}
                    </span>
                  )}
                </div>
                {article.place_name && (
                  <p className="text-sm text-blue-600 font-medium mb-2">📍 {article.place_name}</p>
                )}
                <p className="text-gray-600 mb-2 line-clamp-3 flex-1">{article.summary}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-500 mt-auto pt-2">
                  {article.city_hints && (
                    <span>📍 {JSON.parse(article.city_hints)[0]}</span>
                  )}
                  {article.tags && JSON.parse(article.tags).length > 0 && (
                    <span>🏷️ {JSON.parse(article.tags).slice(0, 2).join(', ')}</span>
                  )}
                </div>
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// 羊毛 (Deals) Tab - Food coupons and discounts
function DealsTab() {
  const [coupons, setCoupons] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDeals()
  }, [])

  const fetchDeals = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/feeds/deals`)
      if (res.ok) {
        const data = await res.json()
        setCoupons(data.coupons || [])
      } else {
        console.error('Error fetching deals feed:', res.status, res.statusText)
        setCoupons([])
      }
    } catch (error) {
      console.error('Error fetching deals:', error)
      setCoupons([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-8">Loading deals...</div>

  return (
    <div className="space-y-4">
      {coupons.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p className="mb-2">暂无优惠券。</p>
          <p className="text-sm">优惠券搜索任务每天自动运行，或等待配额重置后手动触发。</p>
          <p className="text-xs mt-2 text-gray-400">提示：Google CSE API 每日配额有限，可能需要等待配额重置。</p>
        </div>
      ) : (
        <div 
          style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '1.5rem'
          }}
        >
          {coupons.map((coupon) => (
            <div key={coupon.id} className="bg-white rounded-lg shadow overflow-hidden hover:shadow-lg transition flex flex-col">
              {/* Media Section */}
              {coupon.video_url && (
                <div className="w-full" style={{ position: 'relative', paddingBottom: '56.25%', height: 0 }}>
                  {coupon.video_url.includes('youtube.com') || coupon.video_url.includes('youtu.be') ? (
                    // YouTube embed
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
                          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
                        />
                      ) : (
                        <a href={coupon.video_url} target="_blank" rel="noopener noreferrer" className="block w-full h-full bg-gray-200 flex items-center justify-center">
                          <span className="text-gray-600">点击观看视频</span>
                        </a>
                      );
                    })()
                  ) : (
                    // Other video (use video tag)
                    <video
                      src={coupon.video_url}
                      controls
                      className="w-full h-full object-cover"
                      style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
                    />
                  )}
                </div>
              )}
              {!coupon.video_url && coupon.image_url && (
                <div className="w-full h-48 overflow-hidden bg-gray-200">
                  <img
                    src={coupon.image_url}
                    alt={coupon.title || 'Coupon image'}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
              )}
              
              {/* Content Section */}
              <div className="p-6 flex-1 flex flex-col">
                <h3 className="text-lg font-semibold mb-2">{coupon.title}</h3>
                {coupon.code && (
                  <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-3">
                    <p className="text-sm text-gray-600 mb-1">优惠码:</p>
                    <p className="text-blue-600 font-bold text-lg">{coupon.code}</p>
                  </div>
                )}
                {coupon.city && (
                  <p className="text-sm text-gray-600 mb-2">📍 {coupon.city}</p>
                )}
                {coupon.category && (
                  <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded mb-2">
                    {coupon.category}
                  </span>
                )}
                {coupon.terms && (
                  <p className="text-sm text-gray-600 mb-3 flex-1" style={{ 
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden'
                  }}>{coupon.terms}</p>
                )}
                {coupon.source_url && (
                  <a
                    href={coupon.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block text-blue-600 hover:underline text-sm font-medium mt-auto"
                  >
                    查看详情 →
                  </a>
                )}
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
function WealthTab() {
  const [videos, setVideos] = useState<any[]>([])
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [portfolioLoading, setPortfolioLoading] = useState(true)
  const [sortColumn, setSortColumn] = useState<string | null>('value')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')
  const [intradayDataCache, setIntradayDataCache] = useState<Record<string, any[]>>({})
  const videoCarouselRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchWealth()
    loadPortfolio()
  }, [])

  const fetchWealth = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/feeds/wealth`)
      if (res.ok) {
        const data = await res.json()
        setVideos(data.articles || [])
      } else {
        console.error('Error fetching wealth feed:', res.status, res.statusText)
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
        console.log('Portfolio data loaded:', data)
        console.log('Holdings count:', data.holdings?.length)
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
          console.error(`Error loading intraday data for ${holding.ticker}:`, error)
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
    const areaPath = `M ${padding},${height - padding} L ${points.split(' ').map((p, i) => {
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

  const scrollCarousel = (direction: 'left' | 'right') => {
    if (videoCarouselRef.current) {
      const scrollAmount = 400
      const currentScroll = videoCarouselRef.current.scrollLeft
      const newScroll = direction === 'left' ? currentScroll - scrollAmount : currentScroll + scrollAmount
      videoCarouselRef.current.scrollLeft = newScroll
    }
  }

  if (loading && portfolioLoading) return <div className="text-center py-8">Loading...</div>

  return (
    <div className="space-y-8">
      {/* Portfolio Summary Section - Google Finance Style */}
      {portfolioData && Array.isArray(portfolioData.holdings) && portfolioData.holdings.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          {/* Portfolio Header */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold mb-2">我的投资组合</h2>
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
                {getSortedHoldings().map((holding: any, index: number) => (
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
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Video Carousel Section */}
      <div>
        <h2 className="text-2xl font-bold mb-4">热门投资视频</h2>
        {videos.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            暂无内容。后台任务运行后会显示美股投资视频。
          </div>
        ) : (
          <div className="relative">
            {/* Left scroll button */}
            <button
              onClick={() => scrollCarousel('left')}
              className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition"
              style={{ marginLeft: '-20px' }}
            >
              <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            {/* Right scroll button */}
            <button
              onClick={() => scrollCarousel('right')}
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
    </div>
  )
}

// 八卦 (Gossip) Tab - Trending posts from 1point3acres and Teamblind
function GossipTab() {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchGossip()
  }, [])

  const fetchGossip = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/feeds/gossip`)
      if (res.ok) {
        const data = await res.json()
        setArticles(data.articles || [])
      } else {
        console.error('Error fetching gossip feed:', res.status, res.statusText)
        setArticles([])
      }
    } catch (error) {
      console.error('Error fetching gossip:', error)
      setArticles([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-8">Loading gossip...</div>

  return (
    <div className="space-y-4">
      {articles.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          暂无内容。后台任务运行后会显示热门帖子。
        </div>
      ) : (
        <div className="grid gap-4">
          {articles.map((article) => (
            <Link
              key={article.id}
              href={`/article/${article.id}`}
              className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition block"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold flex-1">{article.title}</h3>
                <span className="ml-2 px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-800">
                  {article.source_type === 'di_li' ? '1point3acres' : 'Teamblind'}
                </span>
              </div>
              <p className="text-gray-600 mb-2">{article.summary}</p>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span>热度: {article.final_score.toFixed(2)}</span>
                {article.city_hints && (
                  <span>📍 {JSON.parse(article.city_hints)[0]}</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

