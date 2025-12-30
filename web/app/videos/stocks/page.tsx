/**
 * Stock Analysis Videos Page - Placeholder
 */
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: '美股分析视频 | 湾区牛马日常',
  description: '美股分析视频合集',
}

export default function StockVideosPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">📺 美股分析视频</h1>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-600">此页面正在开发中，敬请期待。</p>
        </div>
      </div>
    </div>
  )
}

