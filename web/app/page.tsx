import { Metadata } from 'next'
import { TabNavigation } from './components/TabNavigation'
import { FinancialSummaryBar } from './components/home/FinancialSummaryBar'
import { TechCatalystNewsCard } from './components/home/TechCatalystNewsCard'
import { StockAnalysisRow } from './components/home/StockAnalysisRow'
import { YouTubeCarousel } from './components/home/YouTubeCarousel'
import { CollapsibleSection } from './components/home/CollapsibleSection'
import { TodayRemindersSection } from './components/home/TodayRemindersSection'
import { PlaceCarousel } from './components/PlaceCarousel'
import { DealsCarousel } from './components/DealsCarousel'
import { EntertainmentCarousel } from './components/EntertainmentCarousel'
import { GossipCarousel } from './components/GossipCarousel'
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
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 space-y-3">
        {/* (1) Financial Summary Bar - Single Banner (Full Width, <= 64px) */}
        <FinancialSummaryBar />

        {/* (2) Today Reminders - Collapsible Section */}
        <CollapsibleSection title="⚠️ 今天必须做的事" defaultCollapsed={true}>
          <TodayRemindersSection />
        </CollapsibleSection>

        {/* (4) News & Videos Row - Secondary Priority (6/6 layout) */}
        <div className="grid grid-cols-12 gap-3">
          {/* Left: Tech News (Text-only, no thumbnails) */}
          <div className="col-span-12 lg:col-span-6 flex">
            <TechCatalystNewsCard />
          </div>

          {/* Right: Tech Videos (Max 3 thumbnails) */}
          <div className="col-span-12 lg:col-span-6 flex">
            <YouTubeCarousel
              category="tech"
              title="📺 科技新闻解读"
              viewMoreHref="/videos/tech"
              limit={3}
            />
          </div>
        </div>

        {/* (5) Stock Analysis Videos Row - Secondary Priority (6/6 layout) */}
        <StockAnalysisRow />

        {/* (6-9) Lifestyle Content - Tertiary Priority (Collapsed by default) */}
        <CollapsibleSection title="🍜 吃点好的" defaultCollapsed={true}>
          <PlaceCarousel
            title=""
            cuisineType="chinese"
            viewMoreHref="/food?cuisine_type=chinese"
          />
        </CollapsibleSection>

        <CollapsibleSection title="🧋 肥宅快乐水" defaultCollapsed={true}>
          <PlaceCarousel
            title=""
            cuisineType="boba"
            viewMoreHref="/food?cuisine_type=boba"
          />
        </CollapsibleSection>

        <CollapsibleSection title="💰 遍地羊毛" defaultCollapsed={true}>
          <DealsCarousel />
        </CollapsibleSection>

        <CollapsibleSection title="🎬 今晚追什么" defaultCollapsed={true}>
          <EntertainmentCarousel hideTitle={true} />
        </CollapsibleSection>

        <CollapsibleSection title="🗣 北美八卦" defaultCollapsed={true}>
          <GossipCarousel hideTitle={true} />
        </CollapsibleSection>
      </div>
    </div>
  )
}
