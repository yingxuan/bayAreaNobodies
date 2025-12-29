import { Metadata } from 'next'
import { TabNavigation } from './components/TabNavigation'
import { HomeOverview } from './components/HomeOverview'
import { FinancialStatusCard } from './components/FinancialStatusCard'
import { TodayMustDo } from './components/TodayMustDo'
import { EntryCards } from './components/EntryCards'
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
        {/* Layer 1: State (10 seconds scan) */}
        <HomeOverview />

        {/* Layer 2: Decision (30 seconds decide) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FinancialStatusCard />
          <TodayMustDo />
        </div>

        {/* Layer 3: Entry (No lists, only entry cards) */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">快速入口</h2>
          <EntryCards />
        </div>
      </div>
    </div>
  )
}
