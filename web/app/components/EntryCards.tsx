/**
 * Entry Cards - Layer 3: Entry Points
 * 6 entry cards: 今天吃什么、新开的奶茶、今日羊毛、最近可以追的、科技&职业雷达、我的资产
 */
'use client'

import { useState, useEffect } from 'react'
import { EntryCard } from './EntryCard'
import { getDealReadableTitle, getDealSaveText } from '../lib/dealFormat'
import { generateConcreteTitle, generateWhatItMeans } from '../lib/techContent'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function EntryCards() {
  const [todayEat, setTodayEat] = useState<any>(null)
  const [boba, setBoba] = useState<any>(null)
  const [topDeal, setTopDeal] = useState<any>(null)
  const [entertainment, setEntertainment] = useState<any>(null)
  const [techItems, setTechItems] = useState<any[]>([])
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
        techRes
      ] = await Promise.all([
        fetch(`${API_URL}/food/today-pick?city=cupertino`).catch(() => null),
        fetch(`${API_URL}/food/restaurants?cuisine_type=boba&limit=1`).catch(() => null),
        fetch(`${API_URL}/feeds/deals?limit=1`).catch(() => null),
        fetch(`${API_URL}/deals/food?city=cupertino&limit=1`).catch(() => null),
        fetch(`${API_URL}/tech/trending?source=hn&limit=1`).catch(() => null)
      ])

      if (eatRes?.ok) {
        const data = await eatRes.json()
        setTodayEat(data)
      }

      if (bobaRes?.ok) {
        const data = await bobaRes.json()
        if (data.restaurants?.[0]) {
          setBoba(data.restaurants[0])
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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* 1. 今天吃什么 */}
      <EntryCard
        icon="🍜"
        title="今天吃什么"
        summary={todayEat 
          ? `${todayEat.restaurant?.name || '中餐馆'} · ${todayEat.dish?.name || '招牌菜'}`
          : '暂无推荐'
        }
        href="/food"
        onClick={todayEat?.restaurant?.googleMapsUrl ? () => {
          window.open(todayEat.restaurant.googleMapsUrl, '_blank')
        } : undefined}
        imageUrl={todayEat?.dish?.image}
      />

      {/* 2. 新开的奶茶/饮品 */}
      <EntryCard
        icon="🧋"
        title="新开的奶茶"
        summary={boba 
          ? `${boba.name || '奶茶店'} · ⭐ ${boba.rating?.toFixed(1) || 'N/A'}`
          : '暂无新店'
        }
        href="/food?cuisine_type=boba"
        imageUrl={boba?.photo_url}
      />

      {/* 3. 今日羊毛 */}
      <EntryCard
        icon="💸"
        title="今日羊毛"
        summary={getDealSummary(topDeal)}
        href="/deals"
        badge={topDeal ? '限时' : undefined}
      />

      {/* 4. 最近可以追的 */}
      <EntryCard
        icon="🎬"
        title="最近可以追的"
        summary={getEntertainmentSummary()}
        href="/gossip"
      />

      {/* 5. 科技 & 职业雷达 (only 1 card, showing top item) */}
      <EntryCard
        icon="🧠"
        title="科技 & 职业雷达"
        summary={techItems.length > 0 ? getTechSummary(techItems[0]) : '暂无科技动态'}
        href="/tech"
      />

      {/* 6. 我的资产 */}
      <EntryCard
        icon="💼"
        title="我的资产"
        summary="查看完整持仓和收益"
        href="/wealth"
      />
    </div>
  )
}

