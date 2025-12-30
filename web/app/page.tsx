import { Metadata } from 'next'
import { TabNavigation } from './components/TabNavigation'
import { WealthSection } from './components/home/WealthSection'
import { TechSection } from './components/home/TechSection'
import { LifestyleSection } from './components/home/LifestyleSection'
import { DealsSection } from './components/home/DealsSection'
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
      <div className="mx-auto max-w-6xl px-3 sm:px-4 py-3 sm:py-4 space-y-3">
        {/* Section 1: 早日财富自由 */}
        <WealthSection />

        {/* Section 2: 行业新闻 */}
        <TechSection />

        {/* Section 3: 吃喝玩乐 */}
        <LifestyleSection />

        {/* Section 4: 遍地羊毛 */}
        <DealsSection />
      </div>
    </div>
  )
}
