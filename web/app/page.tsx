import { Metadata } from 'next'
import { TabNavigation } from './components/TabNavigation'
import { TodayCommandBar } from './components/TodayCommandBar'
import { TodayBrief } from './components/TodayBrief'
import { TechRadar } from './components/TechRadar'
import { HomePortfolioSection, HomeRestaurantSection, HomeDealsSection, HomeGossipSection } from './components/HomeSections'
import { SITE_METADATA } from './lib/constants'

export const metadata: Metadata = {
  title: '湾区牛马日常｜湾区码农老中一站式今日简报',
  description: '每日30秒：资产波动、今天吃什么、今日羊毛、热帖TL;DR、避坑提醒。',
  openGraph: {
    title: '湾区牛马日常｜湾区码农老中一站式今日简报',
    description: '每日30秒：资产波动、今天吃什么、今日羊毛、热帖TL;DR、避坑提醒。',
    url: SITE_METADATA.url,
    siteName: '湾区牛马日常',
    images: [
      {
        url: SITE_METADATA.ogImage,
        width: 1200,
        height: 630,
        alt: '湾区牛马日常',
      },
    ],
    locale: 'zh_CN',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: '湾区牛马日常｜湾区码农老中一站式今日简报',
    description: '每日30秒：资产波动、今天吃什么、今日羊毛、热帖TL;DR、避坑提醒。',
    images: [SITE_METADATA.ogImage],
  },
}

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <TabNavigation activeTab="home" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Today Command Bar - Top Priority */}
        <TodayCommandBar />
        
        {/* First Screen: Today Brief + Tech Radar (Desktop: side by side, Mobile: stacked) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Today Brief - Card Grid Layout (2/3 width on desktop) */}
          <div className="lg:col-span-8">
            <TodayBrief />
          </div>
          
          {/* Tech Radar (1/3 width on desktop) */}
          <div className="lg:col-span-4">
            <TechRadar />
          </div>
        </div>

        {/* Module 2: Portfolio (Collapsible) */}
        <HomePortfolioSection />

        {/* Module 3: Life Decisions */}
        <div className="space-y-6">
          <HomeRestaurantSection cuisineType="chinese" title="今天吃什么？" />
          <HomeRestaurantSection cuisineType="boba" title="来点冰的甜的！" />
        </div>

        {/* Module 4: Information Radar */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <HomeDealsSection />
          <HomeGossipSection />
        </div>
      </div>
    </div>
  )
}
