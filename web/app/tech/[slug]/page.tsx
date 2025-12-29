import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { getTechItemBySlug } from '../../lib/techNews'
import { SITE_METADATA } from '../../lib/constants'

type Props = {
  params: {
    slug: string
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const item = await getTechItemBySlug(params.slug)
  
  if (!item) {
    return {
      title: '未找到 | 科技圈新动向',
    }
  }

  const description = `${item.what} ${item.why}`.substring(0, 160)
  const url = `${SITE_METADATA.url}/tech/${item.slug}`

  return {
    title: `${item.title} | 科技圈新动向`,
    description,
    openGraph: {
      title: item.title,
      description,
      url,
      siteName: '湾区牛马日常',
      type: 'article',
      publishedTime: item.publishedAt,
      tags: item.tags,
    },
    twitter: {
      card: 'summary_large_image',
      title: item.title,
      description,
    },
  }
}

export default async function TechDetailPage({ params }: Props) {
  const item = await getTechItemBySlug(params.slug)

  if (!item) {
    notFound()
  }

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: item.title,
    description: `${item.what} ${item.why}`,
    datePublished: item.publishedAt || new Date().toISOString(),
    author: {
      '@type': 'Organization',
      name: '湾区牛马日常',
    },
    publisher: {
      '@type': 'Organization',
      name: '湾区牛马日常',
      url: SITE_METADATA.url,
    },
    url: `${SITE_METADATA.url}/tech/${item.slug}`,
    sourceOrganization: {
      '@type': 'Organization',
      name: item.source,
    },
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Back Button */}
          <Link
            href="/tech"
            className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 mb-6"
          >
            ← 返回科技圈新动向
          </Link>

          {/* Header */}
          <div className="bg-white rounded-xl shadow-sm p-6 md:p-8 mb-6 border border-gray-200">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
                  {item.title}
                </h1>
                <div className="flex items-center gap-3 text-sm text-gray-500 mb-4">
                  <span>{item.source}</span>
                  {item.publishedAt && (
                    <span>· {new Date(item.publishedAt).toLocaleDateString('zh-CN', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}</span>
                  )}
                  {item.metrics?.points && (
                    <span>· 🔥 {item.metrics.points} 热度</span>
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
              <div className="flex gap-2 mb-6 flex-wrap">
                {item.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-md"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Summary Bullets */}
            <div className="mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">要点摘要</h2>
              <ul className="space-y-2">
                {item.summaryBullets.map((bullet, idx) => (
                  <li key={idx} className="text-base text-gray-700 flex items-start gap-3">
                    <span className="text-blue-600 mt-1 font-bold">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* What/Why/Action Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-sm font-semibold text-blue-900 mb-2">是什么</div>
                <div className="text-sm text-blue-800">{item.what}</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-sm font-semibold text-green-900 mb-2">为什么关心</div>
                <div className="text-sm text-green-800">{item.why}</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <div className="text-sm font-semibold text-orange-900 mb-2">建议</div>
                <div className="text-sm text-orange-800">{item.action}</div>
              </div>
            </div>

            {/* Metrics */}
            {item.metrics && (
              <div className="flex items-center gap-6 mt-6 pt-6 border-t border-gray-200 text-sm text-gray-600">
                {item.metrics.points && (
                  <span className="flex items-center gap-2">
                    <span>🔥</span>
                    <span>{item.metrics.points} 热度</span>
                  </span>
                )}
                {item.metrics.comments && (
                  <span className="flex items-center gap-2">
                    <span>💬</span>
                    <span>{item.metrics.comments} 评论</span>
                  </span>
                )}
              </div>
            )}

            {/* Source Link */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <a
                href={item.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
              >
                查看原文 →
              </a>
            </div>
          </div>

          {/* More Recommendations */}
          <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">更多科技圈新动向</h2>
            <Link
              href="/tech"
              className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
            >
              查看全部 →
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}

