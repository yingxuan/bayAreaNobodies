'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  console.log('[Home] Component rendering, activeTab:', 'food')
  const [activeTab, setActiveTab] = useState<'food' | 'deals' | 'wealth' | 'gossip'>('food')

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
              { key: 'food', label: '美食' },
              { key: 'deals', label: '羊毛' },
              { key: 'wealth', label: '暴富' },
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
          {activeTab === 'food' && <FoodTab />}
          {activeTab === 'deals' && <DealsTab />}
          {activeTab === 'wealth' && <WealthTab />}
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

// 暴富 (Wealth) Tab - YouTube stock investment videos
function WealthTab() {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchWealth()
  }, [])

  const fetchWealth = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/feeds/wealth`)
      if (res.ok) {
        const data = await res.json()
        setArticles(data.articles || [])
      } else {
        console.error('Error fetching wealth feed:', res.status, res.statusText)
        setArticles([])
      }
    } catch (error) {
      console.error('Error fetching wealth feed:', error)
      setArticles([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-8">Loading investment videos...</div>

  const renderMedia = (article: any) => {
    // YouTube video embed
    if (article.platform === 'youtube' && article.video_id) {
      const embedUrl = `https://www.youtube.com/embed/${article.video_id}?rel=0`
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
    
    // Thumbnail image
    if (article.thumbnail_url) {
      return (
        <div className="w-full rounded-t-lg overflow-hidden">
          <img
            src={article.thumbnail_url}
            alt={article.title || 'Video thumbnail'}
            className="w-full h-48 object-cover"
            onError={(e) => {
              e.currentTarget.style.display = 'none'
            }}
          />
        </div>
      )
    }
    
    return null
  }

  return (
    <div className="space-y-4">
      {articles.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          暂无内容。后台任务运行后会显示美股投资视频。
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
                    <span className="ml-2 px-2 py-1 text-xs font-medium rounded flex-shrink-0 bg-red-100 text-red-800">
                      {article.platform}
                    </span>
                  )}
                </div>
                <p className="text-gray-600 mb-2 line-clamp-3 flex-1">{article.summary}</p>
                {article.published_at && (
                  <div className="text-sm text-gray-500 mt-auto pt-2">
                    {new Date(article.published_at).toLocaleDateString('zh-CN', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </div>
                )}
              </a>
            </div>
          ))}
        </div>
      )}
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

