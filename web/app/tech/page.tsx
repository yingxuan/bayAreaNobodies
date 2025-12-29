import { Metadata } from 'next'
import Link from 'next/link'
import { getTechItems, TECH_LIMIT } from '../lib/techNews'
import { SITE_METADATA } from '../lib/constants'
import { TECH_TAGS, isValidTechTag, getTechTagDisplayName, TechTag } from '../lib/techTags'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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

export default async function TechPage({ 
  searchParams 
}: { 
  searchParams: { source?: string; tag?: string } 
}) {
  // Support both mock techNews and real API
  const source = searchParams?.source || 'hn'
  const selectedTag = searchParams?.tag
  
  let techItems: any[] = []
  let dataSource = 'mock'
  
  // Try to fetch from API first
  if (source === 'hn') {
    try {
      const res = await fetch(`${API_URL}/tech/trending?source=hn&limit=${TECH_LIMIT}`, {
        next: { revalidate: 600 } // 10 minutes cache
      })
      if (res.ok) {
        const apiData = await res.json()
        techItems = apiData.items || []
        dataSource = apiData.dataSource || 'mock'
      }
    } catch (error) {
      console.error('Error fetching tech trending from API:', error)
    }
  }
  
  // Fallback to mock techNews if API fails or source is not hn
  if (techItems.length === 0) {
    techItems = await getTechItems(TECH_LIMIT)
  }
  
  // Filter by tag if specified
  if (selectedTag && isValidTechTag(selectedTag)) {
    techItems = techItems.filter((item: any) => {
      const itemTags = item.tags || []
      return itemTags.includes(selectedTag)
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              🧠 科技圈新动向
            </h1>
            {dataSource === 'mock' && (
              <span className="px-3 py-1 text-xs bg-yellow-50 text-yellow-700 rounded-full">
                Mock Data
              </span>
            )}
          </div>
          <p className="text-gray-600 mb-4">
            湾区码农视角的每日 Tech Brief：AI、大厂动态、投资机会、职业建议
          </p>
          
          {/* Tag Filter Pills */}
          <div className="flex flex-wrap gap-2 mb-4">
            {TECH_TAGS.map((tag) => {
              const isSelected = selectedTag === tag
              const displayName = getTechTagDisplayName(tag)
              return (
                <Link
                  key={tag}
                  href={isSelected ? '/tech' : `/tech/tags/${tag}`}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    isSelected
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {displayName}
                </Link>
              )
            })}
          </div>
          
          {/* Current Filter Status */}
          {selectedTag && isValidTechTag(selectedTag) && (
            <div className="flex items-center gap-2 mb-4">
              <span className="text-sm text-gray-600">
                筛选：<span className="font-semibold">{getTechTagDisplayName(selectedTag)}</span>
              </span>
              <Link
                href="/tech"
                className="text-sm text-blue-600 hover:text-blue-700 underline"
              >
                清除筛选
              </Link>
            </div>
          )}
        </div>

        {/* Tech Items List */}
        <div className="space-y-6">
          {techItems.map((item: any) => {
            // Handle both API format (from /tech/trending) and mock format (from techNews.ts)
            const isApiFormat = item.url && !item.slug
            const itemUrl = isApiFormat ? item.url : `/tech/${item.slug}`
            const itemTitle = item.title
            const itemTags = item.tags || []
            const itemScore = item.score || item.metrics?.points
            const itemComments = item.comments || item.metrics?.comments
            const itemAuthor = item.author
            const itemCreatedAt = item.createdAt || item.publishedAt
            
            return (
              <a
                key={item.id}
                href={itemUrl}
                target={isApiFormat ? "_blank" : undefined}
                rel={isApiFormat ? "noopener noreferrer" : undefined}
                className="block bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-all border border-gray-200"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h2 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                      {itemTitle}
                    </h2>
                    <div className="flex items-center gap-3 text-sm text-gray-500">
                      <span>{item.source || 'Hacker News'}</span>
                      {itemCreatedAt && (
                        <span>· {new Date(itemCreatedAt).toLocaleDateString('zh-CN')}</span>
                      )}
                      {itemScore && (
                        <span>· 🔥 {itemScore}</span>
                      )}
                      {itemComments && (
                        <span>· 💬 {itemComments}</span>
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
                {itemTags.length > 0 && (
                  <div className="flex gap-2 mb-4 flex-wrap">
                    {itemTags.map((tag: string) => (
                      <Link
                        key={tag}
                        href={`/tech/tags/${tag}`}
                        className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                      >
                        {tag}
                      </Link>
                    ))}
                  </div>
                )}

                {/* Summary Bullets (only for mock format) */}
                {item.summaryBullets && item.summaryBullets.length > 0 && (
                  <ul className="space-y-1 mb-4">
                    {item.summaryBullets.map((bullet: string, idx: number) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                        <span className="text-blue-600 mt-1">•</span>
                        <span>{bullet}</span>
                      </li>
                    ))}
                  </ul>
                )}

                {/* What/Why/Action (only for mock format) */}
                {item.what && item.why && item.action && (
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
                )}

                {/* Metrics */}
                {(itemScore || itemComments) && (
                  <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
                    {itemScore && (
                      <span>🔥 {itemScore} 热度</span>
                    )}
                    {itemComments && (
                      <span>💬 {itemComments} 评论</span>
                    )}
                  </div>
                )}
              </a>
            )
          })}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>每日更新 · 湾区码农视角 · 快速决策</p>
        </div>
      </div>
    </div>
  )
}

