'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { BriefItemCard } from './BriefItemCard'
import { generateSlug } from '../lib/slug'
import { DailyBriefItem, DailyBrief } from '../lib/dailyBrief'
import { getTechItems } from '../lib/techNews'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function TodayBrief() {
  const [brief, setBrief] = useState<DailyBrief | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBrief()
  }, [])

  const fetchBrief = async () => {
    // Note: getTechItems is async, but we'll handle it in the items building section
    setLoading(true)
    try {
      // Fetch all data sources in parallel
      // Note: Client components can't use next.revalidate, caching handled by server
      const [portfolioRes, foodRes, dealsRes, gossipRes] = await Promise.all([
        fetch(`${API_URL}/portfolio/db-summary`).catch(() => null),
        fetch(`${API_URL}/food/restaurants?cuisine_type=chinese&limit=1`).catch(() => null),
        fetch(`${API_URL}/feeds/deals?limit=1`).catch(() => null),
        fetch(`${API_URL}/feeds/gossip?limit=1`).catch(() => null),
      ])

      const portfolioData = portfolioRes?.ok ? await portfolioRes.json() : null
      const foodData = foodRes?.ok ? await foodRes.json() : null
      const dealsData = dealsRes?.ok ? await dealsRes.json() : null
      const gossipData = gossipRes?.ok ? await gossipRes.json() : null

      // Build brief items
      const items: DailyBriefItem[] = []

      // 1. Portfolio (Large Card - First Row)
      if (portfolioData) {
        const totalValue = portfolioData.total_value || 0
        const dayGain = portfolioData.day_gain || 0
        const dayGainPercent = portfolioData.day_gain_percent || 0
        const gainSign = dayGain >= 0 ? '+' : ''
        items.push({
          id: 'portfolio',
          type: 'portfolio',
          icon: '💰',
          title: '市场 & 我的钱',
          summary: `总资产 $${totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} | 今日 ${gainSign}$${Math.abs(dayGain).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} (${gainSign}${Math.abs(dayGainPercent || 0).toFixed(2)}%)`,
          ctaText: '查看资产',
          href: '/wealth',
          tags: dayGain >= 0 ? ['📈 上涨'] : ['📉 下跌']
        })
      } else {
        items.push({
          id: 'portfolio-fallback',
          type: 'portfolio',
          icon: '💰',
          title: '市场 & 我的钱',
          summary: '加载中...',
          ctaText: '查看资产',
          href: '/wealth'
        })
      }
      
      // 2. Hot Financial Topic (Large Card - First Row)
      items.push({
        id: 'hot-financial',
        type: 'alert',
        icon: '🔥',
        title: '热点金融',
        summary: '查看实时市场数据：黄金、BTC、利率、彩票',
        ctaText: '查看市场',
        href: '/wealth',
        tags: ['实时']
      })

      // 3. Food (Small Card - Second Row)
      if (foodData?.restaurants?.[0]) {
        const restaurant = foodData.restaurants[0]
        items.push({
          id: `food-${restaurant.id}`,
          type: 'food',
          icon: '🍜',
          title: '今天吃什么',
          summary: `${restaurant.name} | ${restaurant.rating ? `⭐ ${restaurant.rating}` : ''}`,
          ctaText: '查看餐厅',
          href: `/city/cupertino`,
          tags: restaurant.rating ? [`${restaurant.rating}分`] : []
        })
      } else {
        items.push({
          id: 'food-fallback',
          type: 'food',
          icon: '🍜',
          title: '今天吃什么',
          summary: '暂无推荐',
          ctaText: '查看餐厅',
          href: '/food'
        })
      }

      // 4. Deal (Small Card - Second Row)
      if (dealsData?.coupons?.[0]) {
        const deal = dealsData.coupons[0]
        items.push({
          id: `deal-${deal.id}`,
          type: 'deal',
          icon: '🛍',
          title: '今日羊毛',
          summary: deal.title || deal.description || '最新优惠',
          ctaText: '查看羊毛',
          href: `/deals/${deal.source || 'unknown'}/${generateSlug(deal.title || deal.description || '')}-${deal.id}`,
          tags: [
            ...(deal.category ? [deal.category] : []),
            ...(deal.chinese_friendliness_score && deal.chinese_friendliness_score > 0.7 ? ['✅老中实测'] : []),
            ...(deal.score && deal.score > 0.8 ? ['🧪已验证'] : [])
          ]
        })
      } else {
        items.push({
          id: 'deal-fallback',
          type: 'deal',
          icon: '🛍',
          title: '今日羊毛',
          summary: '暂无新羊毛',
          ctaText: '查看羊毛',
          href: '/deals'
        })
      }

      // 5. Gossip/Post (Small Card - Second Row)
      if (gossipData?.articles?.[0]) {
        const article = gossipData.articles[0]
        const snippet = article.snippet || article.summary || article.title || ''
        const bullets = snippet.length > 80 
          ? snippet.substring(0, 80) + '...'
          : snippet
        
        items.push({
          id: `post-${article.id}`,
          type: 'post',
          icon: '🗣',
          title: '今日热帖',
          summary: bullets,
          ctaText: '查看热帖',
          href: `/posts/${article.source || 'unknown'}/${generateSlug(article.title || '')}-${article.id}`,
          tags: [
            ...(article.tags ? (Array.isArray(article.tags) ? article.tags.slice(0, 1) : []) : []),
            ...(article.gossip_score && article.gossip_score > 0.8 ? ['🔥热门'] : [])
          ]
        })
      } else {
        items.push({
          id: 'post-fallback',
          type: 'post',
          icon: '🗣',
          title: '今日热帖',
          summary: '暂无热帖',
          ctaText: '查看热帖',
          href: '/gossip'
        })
      }

      // 6. Tech News (Small Card - Second Row)
      try {
        const techItems = await getTechItems(1)
        if (techItems.length > 0) {
          const techItem = techItems[0]
          items.push({
            id: `tech-${techItem.id}`,
            type: 'alert',
            icon: '🧠',
            title: '科技圈新动向',
            summary: `${techItem.title} | ${techItem.what}`,
            ctaText: '查看详情',
            href: `/tech/${techItem.slug}`,
            tags: [
              ...techItem.tags.slice(0, 1),
              ...(techItem.isBreaking ? ['🔥突发'] : [])
            ]
          })
        } else {
          items.push({
            id: 'tech-fallback',
            type: 'alert',
            icon: '🧠',
            title: '科技圈新动向',
            summary: '暂无新动向',
            ctaText: '查看全部',
            href: '/tech'
          })
        }
      } catch (error) {
        console.error('Error fetching tech news:', error)
        items.push({
          id: 'tech-fallback',
          type: 'alert',
          icon: '🧠',
          title: '科技圈新动向',
          summary: '加载中...',
          ctaText: '查看全部',
          href: '/tech'
        })
      }

      // 7. Alert (Small Card - Second Row)
      items.push({
        id: 'alert',
        type: 'alert',
        icon: '⚠️',
        title: '风险提醒',
        summary: '今日无重要提醒',
        ctaText: '查看提醒',
        href: '#',
        tags: ['正常']
      })

      // Ensure we have at least 7 items (2 large + 5 small minimum)
      while (items.length < 7) {
        items.push({
          id: `fallback-${items.length}`,
          type: 'alert',
          icon: '📌',
          title: '加载中...',
          summary: '数据加载中，请稍候',
          ctaText: '刷新',
          href: '#',
        })
      }

      // Get current date and location
      const now = new Date()
      const location = 'Cupertino' // Can be made configurable

      setBrief({
        dateISO: now.toISOString(),
        location,
        items
      })
    } catch (error) {
      console.error('Error fetching brief:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-8">
        <div className="text-center py-8">加载中...</div>
      </div>
    )
  }

  if (!brief) {
    return null
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 md:p-8">
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
          Today · 湾区码农简报
        </h1>
        <p className="text-sm text-gray-500">
          {brief.location} · {new Date(brief.dateISO).toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })} · {new Date(brief.dateISO).toLocaleDateString('zh-CN', { weekday: 'long' }).replace(/星期/g, '周')}
        </p>
      </div>

      {/* Card Grid Layout: First row 2 large cards, second row 3-4 small cards */}
      <div className="space-y-4">
        {/* First Row: 2 Large Cards (Market/Portfolio + Hot Financial) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {brief.items.slice(0, 2).map((item) => (
            <BriefItemCard key={item.id} item={item} size="large" />
          ))}
        </div>
        
        {/* Second Row: 5 Small Cards (Food / Deal / Post / Tech / Alert) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {brief.items.slice(2).map((item) => (
            <BriefItemCard key={item.id} item={item} size="small" />
          ))}
        </div>
      </div>
    </div>
  )
}

