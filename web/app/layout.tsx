import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '湾区牛马日常',
  description: 'Trending feeds, portfolio, and coupons for Bay Area',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
}

