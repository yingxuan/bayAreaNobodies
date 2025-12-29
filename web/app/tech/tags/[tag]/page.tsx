import { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import { getTechItems, TECH_LIMIT } from '../../../lib/techNews'
import { SITE_METADATA } from '../../../lib/constants'
import { isValidTechTag, getTechTagDisplayName, TECH_TAGS } from '../../../lib/techTags'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function generateMetadata({ params }: { params: { tag: string } }): Promise<Metadata> {
  const tag = decodeURIComponent(params.tag)
  
  if (!isValidTechTag(tag)) {
    return {
      title: '标签不存在 | 科技圈新动向',
    }
  }
  
  const displayName = getTechTagDisplayName(tag)
  
  return {
    title: `${displayName} · 科技圈新动向｜湾区码农 Tech Brief`,
    description: `湾区码农视角的 ${displayName} 相关科技动态：最新趋势、深度分析、投资机会。`,
    openGraph: {
      title: `${displayName} · 科技圈新动向`,
      description: `湾区码农视角的 ${displayName} 相关科技动态。`,
      url: `${SITE_METADATA.url}/tech/tags/${tag}`,
      siteName: '湾区牛马日常',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: `${displayName} · 科技圈新动向`,
      description: `湾区码农视角的 ${displayName} 相关科技动态。`,
    },
  }
}

export default async function TechTagPage({ params }: { params: { tag: string } }) {
  const tag = decodeURIComponent(params.tag)
  
  if (!isValidTechTag(tag)) {
    notFound()
  }
  
  const displayName = getTechTagDisplayName(tag)
  
  // Fetch tech items
  let techItems: any[] = []
  let dataSource = 'mock'
  
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
  
  // Fallback to mock if API fails
  if (techItems.length === 0) {
    techItems = await getTechItems(TECH_LIMIT)
  }
  
  // Filter by tag
  const filteredItems = techItems.filter((item: any) => {
    const itemTags = item.tags || []
    return itemTags.includes(tag)
  })
  
  // Limit to 12 items
  const displayItems = filteredItems.slice(0, 12)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              {displayName} · 科技圈新动向
            </h1>
            {dataSource === 'mock' && (
              <span className="px-3 py-1 text-xs bg-yellow-50 text-yellow-700 rounded-full">
                Mock Data
              </span>
            )}
          </div>
          <p className="text-gray-600 mb-4">
            湾区码农视角的 {displayName} 相关科技动态
          </p>
          
          {/* Back to Tech Home */}
          <Link
            href="/tech"
            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 mb-4"
          >
            ← 返回 Tech 首页
          </Link>
        </div>

        {/* Tech Items List */}
        {displayItems.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">暂无 {displayName} 相关的内容</p>
            <Link
              href="/tech"
              className="mt-4 inline-block text-blue-600 hover:text-blue-700"
            >
              返回 Tech 首页
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {displayItems.map((item: any) => {
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
                  </div>

                  {/* Tags */}
                  {itemTags.length > 0 && (
                    <div className="flex gap-2 mb-4 flex-wrap">
                      {itemTags.map((t: string) => (
                        <Link
                          key={t}
                          href={`/tech/tags/${t}`}
                          onClick={(e) => {
                            e.stopPropagation()
                          }}
                          className={`px-2 py-1 text-xs rounded ${
                            t === tag
                              ? 'bg-blue-600 text-white'
                              : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                          } transition-colors`}
                        >
                          {t}
                        </Link>
                      ))}
                    </div>
                  )}
                </a>
              )
            })}
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>每日更新 · 湾区码农视角 · 快速决策</p>
        </div>
      </div>
      
      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'CollectionPage',
            name: `${displayName} · 科技圈新动向`,
            description: `湾区码农视角的 ${displayName} 相关科技动态`,
            url: `${SITE_METADATA.url}/tech/tags/${tag}`,
            mainEntity: {
              '@type': 'ItemList',
              numberOfItems: displayItems.length,
              itemListElement: displayItems.map((item: any, index: number) => ({
                '@type': 'ListItem',
                position: index + 1,
                item: {
                  '@type': 'Article',
                  headline: item.title,
                  url: item.url || `${SITE_METADATA.url}/tech/${item.slug}`,
                  datePublished: item.createdAt || item.publishedAt,
                },
              })),
            },
          }),
        }}
      />
    </div>
  )
}

