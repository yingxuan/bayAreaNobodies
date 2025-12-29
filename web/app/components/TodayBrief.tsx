'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { BriefItemCard } from './BriefItemCard'
import { RiskStatusLight } from './RiskStatusLight'
import { generateSlug } from '../lib/slug'
import { DailyBriefItem, DailyBrief } from '../lib/dailyBrief'
import { fetchHotTopics, HotTopic } from '../lib/hotTopics'
import { getRiskItems, RiskItem } from '../lib/risk'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Generate actionable financial conclusion from market data
 * Must NOT repeat specific numbers from CommandBar
 * Must answer "So-what" - whether action is needed
 */
function generateFinancialConclusion(
  portfolioData: any,
  marketTopic: HotTopic | undefined,
  btcTopic: HotTopic | undefined,
  goldTopic: HotTopic | undefined,
  mortgageTopic: HotTopic | undefined,
  lotteryTopic: HotTopic | undefined
): string {
  // 生成具体的中文解读型结论，包含市场影响分析
  const conclusionParts: string[] = []
  
  if (portfolioData) {
    const dayGainPercent = portfolioData.day_gain_percent || 0
    const absPercent = Math.abs(dayGainPercent)
    
    // 资产表现描述
    if (absPercent > 3) {
      conclusionParts.push(dayGainPercent > 0 
        ? '资产大幅上涨'
        : '资产大幅下跌')
    } else if (absPercent > 1) {
      conclusionParts.push(dayGainPercent > 0 
        ? '资产小幅上涨'
        : '资产小幅下跌')
    } else if (absPercent > 0.1) {
      conclusionParts.push(dayGainPercent > 0 
        ? '资产微涨'
        : '资产微跌')
    } else {
      conclusionParts.push('资产基本持平')
    }
    
    // 市场影响分析（不重复 CommandBar 的具体数字）
    const marketFactors: string[] = []
    if (marketTopic && marketTopic.changePercent) {
      const marketChg = parseFloat(marketTopic.changePercent.replace('%', '').replace('+', ''))
      if (Math.abs(marketChg) > 0.5) {
        marketFactors.push(marketChg > 0 ? '主要受美股上涨影响' : '主要受美股回调影响')
      }
    }
    if (btcTopic && btcTopic.changePercent) {
      const btcChg = parseFloat(btcTopic.changePercent.replace('%', '').replace('+', ''))
      if (Math.abs(btcChg) > 2) {
        marketFactors.push(btcChg > 0 ? 'BTC 上涨带动' : 'BTC 回调拖累')
      }
    }
    
    if (marketFactors.length > 0) {
      conclusionParts.push(marketFactors.join('，'))
    } else {
      conclusionParts.push('市场整体平稳')
    }
  } else {
    // 无资产数据时，只显示市场情况
    if (marketTopic && marketTopic.changePercent) {
      const marketChg = parseFloat(marketTopic.changePercent.replace('%', '').replace('+', ''))
      if (Math.abs(marketChg) > 0.5) {
        conclusionParts.push(marketChg > 0 ? '今日美股上涨' : '今日美股回调')
      } else {
        conclusionParts.push('市场整体平稳')
      }
    } else {
      conclusionParts.push('市场整体平稳')
    }
  }
  
  return conclusionParts.join('，')
}

export function TodayBrief() {
  const [brief, setBrief] = useState<DailyBrief | null>(null)
  const [loading, setLoading] = useState(true)
  const [hotTopics, setHotTopics] = useState<HotTopic[]>([])
  const [riskItems, setRiskItems] = useState<RiskItem[]>([])

  useEffect(() => {
    fetchBrief()
    fetchHotTopicsData()
    fetchRiskItems()
  }, [])

  const fetchHotTopicsData = async () => {
    try {
      const topics = await fetchHotTopics()
      setHotTopics(topics)
    } catch (error) {
      console.error('Error fetching hot topics:', error)
    }
  }

  const fetchRiskItems = async () => {
    try {
      const risks = await getRiskItems('cupertino')
      setRiskItems(risks)
    } catch (error) {
      console.error('Error fetching risk items:', error)
      setRiskItems([]) // Never throw, show empty state
    }
  }

  const fetchBrief = async () => {
    setLoading(true)
    try {
      // Fetch all data sources in parallel
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

      // Get market data from hotTopics
      const marketTopic = hotTopics.find((t: HotTopic) => t.id === 'market')
      const btcTopic = hotTopics.find((t: HotTopic) => t.id === 'btc')
      const goldTopic = hotTopics.find((t: HotTopic) => t.id === 'gold')
      const mortgageTopic = hotTopics.find((t: HotTopic) => t.id === 'jumbo_arm')
      const lotteryTopic = hotTopics.find((t: HotTopic) => t.id === 'lottery')

      // Build brief items
      const items: DailyBriefItem[] = []

      // 1. Financial Conclusion (Large Card) - Must show total value (only place on first screen)
      // 必须显示三行（顺序固定）：总资产 | 今日涨跌 | 解读型结论
      const totalValue = portfolioData?.total_value || 0
      const dayGain = portfolioData?.day_gain || 0
      const dayGainPercent = portfolioData?.day_gain_percent || 0
      
      // 第一行：总资产：$X,XXX,XXX（必须显示）
      const summaryLines: string[] = []
      summaryLines.push(`总资产：$${totalValue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`)
      
      // 第二行：今日涨跌：+$Y,YYY（+Z.ZZ%）（必须显示，如果 portfolio data 存在）
      if (portfolioData) {
        // 处理符号：正数显示 +，负数显示 -，0 不显示符号
        const absDayGain = Math.abs(dayGain)
        const absDayGainPercent = Math.abs(dayGainPercent)
        
        let gainSign = ''
        if (dayGain > 0) {
          gainSign = '+'
        } else if (dayGain < 0) {
          gainSign = '-'
        }
        // dayGain === 0 时，gainSign 保持为空字符串
        
        let percentSign = ''
        if (dayGainPercent > 0) {
          percentSign = '+'
        } else if (dayGainPercent < 0) {
          percentSign = '-'
        }
        
        // 如果 dayGain 和 dayGainPercent 都是 0，显示为 $0（0.00%）
        if (absDayGain < 0.01 && absDayGainPercent < 0.01) {
          summaryLines.push(`今日涨跌：$0（0.00%）`)
        } else {
          summaryLines.push(`今日涨跌：${gainSign}$${absDayGain.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}（${percentSign}${absDayGainPercent.toFixed(2)}%）`)
        }
      } else {
        summaryLines.push(`今日涨跌：数据加载中...`)
      }
      
      // 第三行：解读型结论（必须显示，中文）
      const financialConclusion = generateFinancialConclusion(
        portfolioData,
        marketTopic,
        btcTopic,
        goldTopic,
        mortgageTopic,
        lotteryTopic
      )
      if (financialConclusion && financialConclusion !== '数据加载中...') {
        summaryLines.push(financialConclusion)
      } else {
        summaryLines.push('数据加载中...')
      }

      items.push({
        id: 'financial-conclusion',
        type: 'portfolio',
        icon: '💰',
        title: '财务结论',
        summary: summaryLines.join(' | '),
        ctaText: '查看资产',
        href: '/wealth',
        tags: portfolioData && portfolioData.day_gain >= 0 ? ['📈 上涨'] : portfolioData ? ['📉 下跌'] : []
      })

      // 2-4. Entry Cards (Small Cards) - Only one-line summary, no images/lists
      // 2. Food Entry
      if (foodData?.restaurants?.[0]) {
        const restaurant = foodData.restaurants[0]
        items.push({
          id: `food-${restaurant.id}`,
          type: 'food',
          icon: '🍜',
          title: '今天吃什么',
          summary: `Cupertino 中餐 Top Pick: ${restaurant.name}${restaurant.rating ? ` ⭐${restaurant.rating}` : ''}`,
          ctaText: '查看',
          href: `/city/cupertino`,
          tags: []
        })
      } else {
        items.push({
          id: 'food-fallback',
          type: 'food',
          icon: '🍜',
          title: '今天吃什么',
          summary: '暂无推荐',
          ctaText: '查看',
          href: '/food'
        })
      }

      // 3. Deal Entry
      if (dealsData?.coupons?.[0]) {
        const deal = dealsData.coupons[0]
        const dealTitle = deal.title || deal.description || '最新优惠'
        const dealSummary = dealTitle.length > 50 ? dealTitle.substring(0, 50) + '...' : dealTitle
        items.push({
          id: `deal-${deal.id}`,
          type: 'deal',
          icon: '🛍',
          title: '羊毛精选',
          summary: dealSummary,
          ctaText: '查看',
          href: `/deals/${deal.source || 'unknown'}/${generateSlug(deal.title || deal.description || '')}-${deal.id}`,
          tags: []
        })
      } else {
        items.push({
          id: 'deal-fallback',
          type: 'deal',
          icon: '🛍',
          title: '羊毛精选',
          summary: '暂无新羊毛',
          ctaText: '查看',
          href: '/deals'
        })
      }

      // 4. Gossip/Post Entry
      if (gossipData?.articles?.[0]) {
        const article = gossipData.articles[0]
        const sourceName = article.source === '1point3acres' ? '一亩三分地' : article.source === 'teamblind' ? 'Blind' : article.source || '热帖'
        const snippet = article.snippet || article.summary || article.title || ''
        const summary = snippet.length > 50 
          ? `${sourceName}：${snippet.substring(0, 50)}...`
          : `${sourceName}：${snippet}`
        
        items.push({
          id: `post-${article.id}`,
          type: 'post',
          icon: '🗣',
          title: '热帖精选',
          summary: summary,
          ctaText: '查看',
          href: `/posts/${article.source || 'unknown'}/${generateSlug(article.title || '')}-${article.id}`,
          tags: []
        })
      } else {
        items.push({
          id: 'post-fallback',
          type: 'post',
          icon: '🗣',
          title: '热帖精选',
          summary: '暂无热帖',
          ctaText: '查看',
          href: '/gossip'
        })
      }

      // Get current date and location
      const now = new Date()
      const location = 'Cupertino'

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

  // Re-fetch when hotTopics or riskItems change
  useEffect(() => {
    if (hotTopics.length > 0 || riskItems.length >= 0) {
      fetchBrief()
    }
  }, [hotTopics, riskItems])

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
          湾区码农简报
        </h1>
        <p className="text-sm text-gray-500">
          {brief.location} · {new Date(brief.dateISO).toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })} · {new Date(brief.dateISO).toLocaleDateString('zh-CN', { weekday: 'long' }).replace(/星期/g, '周')}
        </p>
      </div>

      {/* Layout: 1 conclusion + 3 entry cards + 1 risk status light */}
      <div className="space-y-4">
        {/* Financial Conclusion (Large Card) */}
        <div className="grid grid-cols-1 gap-4">
          {brief.items.slice(0, 1).map((item) => (
            <BriefItemCard key={item.id} item={item} size="large" />
          ))}
        </div>
        
        {/* Entry Cards (3 Small Cards) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {brief.items.slice(1).map((item) => (
            <BriefItemCard key={item.id} item={item} size="small" />
          ))}
        </div>

        {/* Risk Status Light (Horizontal Bar) */}
        <RiskStatusLight risks={riskItems} />
      </div>
    </div>
  )
}
