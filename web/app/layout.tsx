import type { Metadata } from 'next'
import './globals.css'
import { SITE_METADATA } from './lib/constants'

export const metadata: Metadata = {
  metadataBase: new URL(SITE_METADATA.url),
  title: SITE_METADATA.title,
  description: SITE_METADATA.description,
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

