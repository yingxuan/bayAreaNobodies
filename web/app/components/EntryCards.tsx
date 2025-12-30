/**
 * Entry Cards - Layer 3: Entry Points
 * 6 entry cards: 今天吃什么、新开的奶茶、今日羊毛、最近可以追的、科技&职业雷达、我的资产
 */
'use client'

import { useState, useEffect } from 'react'
import { EntryCard } from './EntryCard'
import { getDealReadableTitle, getDealSaveText } from '../lib/dealFormat'
import { generateConcreteTitle, generateWhatItMeans, generateWhatHappened, generateWhatYouCanDo } from '../lib/techContent'

// Extract entity helper (duplicated from techContent.ts for use in component)
function extractEntity(title: string): { company: string | null; product: string | null } {
  const titleLower = title.toLowerCase()
  const companies: Record<string, string> = {
    'google': 'Google',
    'openai': 'OpenAI',
    'anthropic': 'Anthropic',
    'meta': 'Meta',
    'facebook': 'Meta',
    'microsoft': 'Microsoft',
    'amazon': 'Amazon',
    'aws': 'AWS',
    'nvidia': 'NVIDIA',
    'apple': 'Apple',
  }
  let company: string | null = null
  for (const [key, value] of Object.entries(companies)) {
    if (titleLower.includes(key)) {
      company = value
      break
    }
  }
  return { company, product: null }
}
import { getDealImage } from '../lib/dealImage'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function EntryCards() {
  const [todayEat, setTodayEat] = useState<any>(null)
  const [todayEatPool, setTodayEatPool] = useState<any[]>([])
  const [todayEatIndex, setTodayEatIndex] = useState(0)
  
  const [boba, setBoba] = useState<any>(null)
  const [bobaPool, setBobaPool] = useState<any[]>([])
  const [bobaIndex, setBobaIndex] = useState(0)
  
  const [topDeal, setTopDeal] = useState<any>(null)
  const [entertainment, setEntertainment] = useState<any>(null)
  const [techItems, setTechItems] = useState<any[]>([])
  const [gossipItem, setGossipItem] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAll()
  }, [])

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [
        eatRes,
        bobaRes,
        dealsRes,
        foodDealsRes,
        techRes,
        gossipRes
      ] = await Promise.all([
        fetch(`${API_URL}/food/today-pick?city=cupertino`).catch(() => null),
        fetch(`${API_URL}/food/restaurants?cuisine_type=boba&limit=10`).catch(() => null),
        fetch(`${API_URL}/feeds/deals?limit=1`).catch(() => null),
        fetch(`${API_URL}/deals/food?city=cupertino&limit=1`).catch(() => null),
        fetch(`${API_URL}/tech/trending?source=hn&limit=1`).catch(() => null),
        fetch(`${API_URL}/feeds/gossip?limit=1`).catch(() => null)
      ])

      // Today Eat - fetch pool for "换一个" feature
      if (eatRes?.ok) {
        const data = await eatRes.json()
        setTodayEat(data)
        // For now, we'll use the same data as pool (in real implementation, fetch multiple)
        setTodayEatPool([data])
      }

      // Boba - fetch pool (10 items) for "换一个" feature
      if (bobaRes?.ok) {
        const data = await bobaRes.json()
        const restaurants = data.restaurants || []
        setBobaPool(restaurants)
        if (restaurants.length > 0) {
          setBoba(restaurants[0])
        }
      }

      // Gossip
      if (gossipRes?.ok) {
        const data = await gossipRes.json()
        if (data.articles?.[0]) {
          setGossipItem(data.articles[0])
        }
      }

      // Prioritize food deals, then retail deals
      let selectedDeal = null
      if (foodDealsRes?.ok) {
        const foodData = await foodDealsRes.json()
        if (foodData.items?.[0]) {
          selectedDeal = foodData.items[0]
        }
      }
      
      if (!selectedDeal && dealsRes?.ok) {
        const data = await dealsRes.json()
        if (data.coupons?.[0]) {
          selectedDeal = data.coupons[0]
        }
      }
      
      if (selectedDeal) {
        setTopDeal(selectedDeal)
      }

      if (techRes?.ok) {
        const data = await techRes.json()
        setTechItems(data.items || [])
      }
    } catch (error) {
      console.error('Error fetching entry cards:', error)
    } finally {
      setLoading(false)
    }
  }

  // Generate deal summary (must show: what + save amount + threshold)
  const getDealSummary = (deal: any): string => {
    if (!deal) return '暂无新羊毛'
    
    const titleCN = getDealReadableTitle(deal)
    const saveText = getDealSaveText(deal)
    
    // Format: "品牌/商品 · 能省 $X · 门槛"
    const parts: string[] = []
    parts.push(titleCN)
    
    if (saveText) {
      parts.push(saveText.replace('可省 ', '≈ 省 '))
    }
    
    // Extract threshold from deal
    const dealText = `${deal.title || ''} ${deal.description || ''}`.toLowerCase()
    if (dealText.includes('bogo') || dealText.includes('buy one get one')) {
      parts.push('BOGO')
    } else if (dealText.includes('clip') || deal.code) {
      parts.push('需 Clip')
    } else if (dealText.includes('app')) {
      parts.push('需 App')
    }
    
    return parts.join(' · ')
  }

  // Generate tech summary (one line)
  const getTechSummary = (item: any): string => {
    if (!item) return '暂无科技动态'
    
    const title = generateConcreteTitle(item.title, item.tags || [])
    // Use a simplified whatItMeans for entry card (shorter)
    const whatItMeans = generateWhatItMeans(item.title, item.tags || [], title)
    
    // Limit to one concise line
    const summary = `${title} → ${whatItMeans}`
    return summary.length > 60 ? summary.substring(0, 57) + '...' : summary
  }

  // Generate entertainment summary (mock for now)
  const getEntertainmentSummary = (): string => {
    // TODO: Implement when API is available
    return '轻松下饭剧推荐'
  }

  // Handle "换一个" for today eat
  const handleRefreshEat = () => {
    if (todayEatPool.length > 0) {
      // For now, just re-fetch (in real implementation, shuffle pool)
      fetch(`${API_URL}/food/today-pick?city=cupertino`)
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data) {
            setTodayEat(data)
          }
        })
        .catch(() => {})
    }
  }

  // Handle "换一个" for boba
  const handleRefreshBoba = () => {
    if (bobaPool.length > 1) {
      // Randomly select from pool
      const newIndex = (bobaIndex + 1) % bobaPool.length
      setBobaIndex(newIndex)
      setBoba(bobaPool[newIndex])
    } else if (bobaPool.length === 1) {
      // Re-fetch if only one item
      fetch(`${API_URL}/food/restaurants?cuisine_type=boba&limit=10`)
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          const restaurants = data?.restaurants || []
          if (restaurants.length > 0) {
            setBobaPool(restaurants)
            setBoba(restaurants[0])
            setBobaIndex(0)
          }
        })
        .catch(() => {})
    }
  }

  // Generate gossip summary
  const getGossipSummary = (gossip: any): string => {
    if (!gossip) return '暂无八卦'
    
    const title = gossip.title || ''
    const source = gossip.source === '1point3acres' ? '一亩三分地' 
      : gossip.source === 'huaren' ? '华人网'
      : gossip.source === 'blind' ? 'Blind'
      : '热帖'
    
    // Truncate title if too long
    const shortTitle = title.length > 30 ? title.substring(0, 27) + '...' : title
    
    return `${shortTitle} ｜ ${source}`
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm p-4 border border-gray-200">
            <div className="h-20 bg-gray-100 rounded animate-pulse" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <>
      {/* Tech Radar - High-density single-line card */}
      {techItems.length > 0 && (
        <div className="mb-4">
          <a 
            href="/tech" 
            className="block bg-white rounded-xl shadow-sm p-4 border border-blue-200 hover:shadow-md transition-all"
          >
            {(() => {
              const item = techItems[0]
              const title = generateConcreteTitle(item.title, item.tags || [])
              const whatHappened = generateWhatHappened(item.title, item.tags || [], title)
              const whatItMeans = generateWhatItMeans(item.title, item.tags || [], whatHappened)
              const whatYouCanDo = generateWhatYouCanDo(item.title, item.tags || [], whatHappened)
              
              // Extract company/theme from title
              const { company } = extractEntity(item.title)
              const companyOrTheme = company || title.split(' ')[0] || '科技'
              
              return (
                <div className="space-y-1.5">
                  {/* First line: Title */}
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-bold text-gray-900">
                      🧠 科技 / 职业雷达 · 今天值得你花 30 秒看的事
                    </p>
                    <span className="text-xs text-blue-600">查看详情 →</span>
                  </div>
                  
                  {/* Second line: What happened */}
                  <p className="text-sm text-gray-800">
                    <span className="font-semibold">【{companyOrTheme}】</span> {whatHappened || title}
                  </p>
                  
                  {/* Third line: What it means (highlighted) */}
                  <p className="text-sm text-blue-700 font-medium">
                    👉 {whatItMeans}
                  </p>
                  
                  {/* Fourth line: What you can do (optional, weakened) */}
                  {whatYouCanDo && (
                    <p className="text-xs text-gray-500">
                      你可以考虑：{whatYouCanDo}
                    </p>
                  )}
                </div>
              )
            })()}
          </a>
        </div>
      )}

      {/* Entry Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 1. 今天吃什么 - with refresh, enhanced */}
        <EntryCard
          icon="🍜"
          title="不想做饭？吃这个"
          summary={todayEat 
            ? `${todayEat.restaurant?.name || '中餐馆'}`
            : '暂无推荐'
          }
          href="/food"
          onClick={todayEat?.restaurant?.googleMapsUrl ? () => {
            window.open(todayEat.restaurant.googleMapsUrl, '_blank')
          } : undefined}
          imageUrl={todayEat?.dish?.image}
          showRefresh={true}
          onRefresh={handleRefreshEat}
          highlightReason={todayEat 
            ? `${todayEat.dish?.name || '招牌菜'} · ⭐ ${todayEat.restaurant?.rating?.toFixed(1) || 'N/A'} · ${todayEat.city || 'Cupertino'}`
            : undefined
          }
          imageHeight="large"
        />

        {/* 2. 新开的奶茶/饮品 - with refresh, enhanced */}
        <EntryCard
          icon="🧋"
          title="今天可以试试的新奶茶"
          summary={boba 
            ? `${boba.name || '奶茶店'}`
            : '暂无新店'
          }
          href="/food?cuisine_type=boba"
          imageUrl={boba?.photo_url}
          showRefresh={true}
          onRefresh={handleRefreshBoba}
          highlightReason={boba 
            ? `⭐ ${boba.rating?.toFixed(1) || 'N/A'} · ${boba.city || 'Cupertino'}`
            : undefined
          }
          imageHeight="large"
        />

        {/* 3. 今日羊毛 - enhanced */}
        <EntryCard
          icon="💰"
          title="今天不薅就亏了的羊毛"
          summary={topDeal 
            ? getDealReadableTitle(topDeal)
            : '暂无新羊毛'
          }
          href="/deals"
          badge={topDeal ? '限时' : undefined}
          imageUrl={topDeal ? getDealImage(topDeal).src : undefined}
          highlightReason={topDeal 
            ? (() => {
                const saveText = getDealSaveText(topDeal)
                const dealText = `${topDeal.title || ''} ${topDeal.description || ''}`.toLowerCase()
                const parts: string[] = []
                if (saveText) {
                  parts.push(saveText.replace('可省 ', '可省 '))
                }
                if (dealText.includes('bogo') || dealText.includes('buy one get one')) {
                  parts.push('BOGO')
                } else if (dealText.includes('clip') || topDeal.code) {
                  parts.push('需 Clip')
                } else if (dealText.includes('app')) {
                  parts.push('需 App')
                }
                return parts.join(' · ')
              })()
            : undefined
          }
          imageHeight="large"
        />

        {/* 4. 最近可以追的 */}
        <EntryCard
          icon="🎬"
          title="最近可以追的"
          summary={getEntertainmentSummary()}
          href="/gossip"
        />

        {/* 5. 今日八卦 */}
        <EntryCard
          icon="💬"
          title="今日八卦"
          summary={getGossipSummary(gossipItem)}
          href="/gossip"
        />

        {/* 6. 我的资产 */}
        <EntryCard
          icon="💼"
          title="我的资产"
          summary="查看完整持仓和收益"
          href="/wealth"
        />
      </div>
    </>
  )
}

