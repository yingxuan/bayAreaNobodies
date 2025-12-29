import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { SITE_METADATA } from '../../lib/constants'
import { generateSlug } from '../../lib/slug'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getDealBySlug(source: string, slug: string) {
  try {
    const res = await fetch(`${API_URL}/feeds/deals?limit=100`, {
      next: { revalidate: 600 }
    })
    if (res.ok) {
      const data = await res.json()
      // Support both slug and id formats
      // 1. Try to extract ID from slug (format: slug-123 or just 123)
      const idMatch = slug.match(/-(\d+)$/)
      const numericId = /^\d+$/.test(slug) ? slug : null
      const extractedId = idMatch ? idMatch[1] : numericId
      
      // 2. If we have an ID, try direct lookup first (for backward compatibility)
      if (extractedId) {
        const byId = data.coupons?.find((d: any) => d.id.toString() === extractedId)
        if (byId) return byId
      }
      
      // 3. Find deal by matching slug
      const deal = data.coupons?.find((d: any) => {
        const dealSlug = generateSlug(d.title || d.description || '')
        const slugWithId = `${dealSlug}-${d.id}`
        return slug === dealSlug || slug === slugWithId || slug.endsWith(`-${d.id}`)
      })
      return deal
    }
  } catch (error) {
    console.error('Error fetching deal:', error)
  }
  return null
}

async function getRelatedDeals(source: string, excludeId: string, limit: number = 3) {
  try {
    const res = await fetch(`${API_URL}/feeds/deals?limit=20`, {
      next: { revalidate: 600 }
    })
    if (res.ok) {
      const data = await res.json()
      return (data.coupons || [])
        .filter((d: any) => d.id.toString() !== excludeId)
        .slice(0, limit)
    }
  } catch (error) {
    console.error('Error fetching related deals:', error)
  }
  return []
}

export async function generateMetadata({ params }: { params: { source: string, slug: string } }): Promise<Metadata> {
  const deal = await getDealBySlug(params.source, params.slug)
  
  if (!deal) {
    return {
      title: '羊毛未找到 | 湾区牛马日常',
    }
  }

  const title = `${deal.title || '羊毛详情'} | ${params.source} | 湾区牛马日常`
  const description = deal.description || deal.snippet || deal.title || '最新羊毛信息'

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url: `${SITE_METADATA.url}/deals/${params.source}/${params.slug}`,
      siteName: '湾区牛马日常',
      images: [SITE_METADATA.ogImage],
      locale: 'zh_CN',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [SITE_METADATA.ogImage],
    },
  }
}

export default async function DealDetailPage({ params }: { params: { source: string, slug: string } }) {
  const [deal, relatedDeals] = await Promise.all([
    getDealBySlug(params.source, params.slug),
    getRelatedDeals(params.source, '', 3)
  ])

  if (!deal) {
    notFound()
  }

  // Filter related deals
  const filteredRelated = relatedDeals.filter((d: any) => d.id.toString() !== deal.id.toString()).slice(0, 3)

  // JSON-LD structured data
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Offer',
    name: deal.title,
    description: deal.description || deal.snippet,
    url: deal.url,
    category: deal.category,
    priceCurrency: 'USD',
    availability: 'https://schema.org/InStock',
    seller: {
      '@type': 'Organization',
      name: deal.source || params.source
    }
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link href="/deals" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← 返回羊毛
          </Link>

          <div className="bg-white rounded-xl shadow-sm p-6 md:p-8">
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">{deal.title || '羊毛详情'}</h1>
              
              {deal.category && (
                <span className="inline-block px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm mb-4">
                  {deal.category}
                </span>
              )}

              <div className="prose max-w-none">
                {deal.description && (
                  <div className="mb-4">
                    <h2 className="text-xl font-semibold mb-2">详情</h2>
                    <p className="text-gray-700 whitespace-pre-wrap">{deal.description}</p>
                  </div>
                )}

                {deal.snippet && !deal.description && (
                  <div className="mb-4">
                    <p className="text-gray-700">{deal.snippet}</p>
                  </div>
                )}

                {deal.source && (
                  <div className="mt-6 text-sm text-gray-600">
                    来源: {deal.source}
                  </div>
                )}

                {deal.url && (
                  <div className="mt-6">
                    <a
                      href={deal.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      查看原文 →
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Related Deals */}
          {filteredRelated.length > 0 && (
            <div className="mt-8 bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-bold mb-4">更多来自 {params.source}</h2>
              <div className="space-y-3">
                {filteredRelated.map((related: any) => {
                  const relatedSlug = generateSlug(related.title || related.description || '')
                  const relatedSlugWithId = `${relatedSlug}-${related.id}`
                  return (
                    <Link
                      key={related.id}
                      href={`/deals/${related.source || 'unknown'}/${relatedSlugWithId}`}
                      className="block p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                    >
                      <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">{related.title}</h3>
                      <p className="text-sm text-gray-600 line-clamp-2">{related.description || related.snippet}</p>
                      {related.category && (
                        <span className="inline-block mt-2 px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">
                          {related.category}
                        </span>
                      )}
                    </Link>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

