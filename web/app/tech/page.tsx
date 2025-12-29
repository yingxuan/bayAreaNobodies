import { Metadata } from 'next'
import Link from 'next/link'
import { getTechItems, TECH_LIMIT } from '../lib/techNews'
import { SITE_METADATA } from '../lib/constants'

export const metadata: Metadata = {
  title: '科技圈新动向｜湾区码农每日 Tech Brief',
  description: '湾区码农视角的科技圈新动向：AI、大厂动态、投资机会、职业建议。每日更新，帮你快速决策。',
  openGraph: {
    title: '科技圈新动向｜湾区码农每日 Tech Brief',
    description: '湾区码农视角的科技圈新动向：AI、大厂动态、投资机会、职业建议。',
    url: `${SITE_METADATA.url}/tech`,
    siteName: '湾区牛马日常',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: '科技圈新动向｜湾区码农每日 Tech Brief',
    description: '湾区码农视角的科技圈新动向：AI、大厂动态、投资机会、职业建议。',
  },
}

export default async function TechPage() {
  const techItems = await getTechItems(TECH_LIMIT)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
            🧠 科技圈新动向
          </h1>
          <p className="text-gray-600">
            湾区码农视角的每日 Tech Brief：AI、大厂动态、投资机会、职业建议
          </p>
        </div>

        {/* Tech Items List */}
        <div className="space-y-6">
          {techItems.map((item) => (
            <Link
              key={item.id}
              href={`/tech/${item.slug}`}
              className="block bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-all border border-gray-200"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h2 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                    {item.title}
                  </h2>
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span>{item.source}</span>
                    {item.publishedAt && (
                      <span>· {new Date(item.publishedAt).toLocaleDateString('zh-CN')}</span>
                    )}
                    {item.metrics?.points && (
                      <span>· {item.metrics.points} 热度</span>
                    )}
                  </div>
                </div>
                {item.isBreaking && (
                  <span className="px-3 py-1 text-xs font-semibold bg-red-100 text-red-700 rounded-full">
                    突发
                  </span>
                )}
              </div>

              {/* Tags */}
              {item.tags.length > 0 && (
                <div className="flex gap-2 mb-4 flex-wrap">
                  {item.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Summary Bullets */}
              <ul className="space-y-1 mb-4">
                {item.summaryBullets.map((bullet, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>

              {/* What/Why/Action */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-100">
                <div>
                  <div className="text-xs font-semibold text-gray-500 mb-1">是什么</div>
                  <div className="text-sm text-gray-700">{item.what}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-gray-500 mb-1">为什么关心</div>
                  <div className="text-sm text-gray-700">{item.why}</div>
                </div>
                <div>
                  <div className="text-xs font-semibold text-gray-500 mb-1">建议</div>
                  <div className="text-sm text-gray-700">{item.action}</div>
                </div>
              </div>

              {/* Metrics */}
              {item.metrics && (
                <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
                  {item.metrics.points && (
                    <span>🔥 {item.metrics.points} 热度</span>
                  )}
                  {item.metrics.comments && (
                    <span>💬 {item.metrics.comments} 评论</span>
                  )}
                </div>
              )}
            </Link>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>每日更新 · 湾区码农视角 · 快速决策</p>
        </div>
      </div>
    </div>
  )
}

