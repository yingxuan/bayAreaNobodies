import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { SITE_METADATA } from '../../lib/constants'
import { generateSlug } from '../../lib/slug'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getPostBySlug(source: string, slug: string) {
  try {
    // Support both slug and id formats
    // 1. Try to extract ID from slug (format: slug-123 or just 123)
    const idMatch = slug.match(/-(\d+)$/)
    const numericId = /^\d+$/.test(slug) ? slug : null
    const extractedId = idMatch ? idMatch[1] : numericId
    
    // 2. If we have an ID, try single article API first (for backward compatibility)
    if (extractedId) {
      try {
        const singleRes = await fetch(`${API_URL}/articles/${extractedId}`, {
          next: { revalidate: 600 }
        })
        if (singleRes.ok) {
          const post = await singleRes.json()
          // Verify slug matches (if not just numeric ID)
          if (numericId || slug.endsWith(`-${post.id}`)) {
            return post
          }
        }
      } catch {
        // Fallback to list API
      }
    }

    // 3. Fallback: use list API
    const res = await fetch(`${API_URL}/feeds/gossip?limit=100`, {
      next: { revalidate: 600 }
    })
    if (res.ok) {
      const data = await res.json()
      
      // If we have an ID, try direct lookup first
      if (extractedId) {
        const byId = data.articles?.find((a: any) => a.id.toString() === extractedId)
        if (byId) return byId
      }
      
      // Find post by matching slug
      const post = data.articles?.find((a: any) => {
        const postSlug = generateSlug(a.title || '')
        const slugWithId = `${postSlug}-${a.id}`
        return slug === postSlug || slug === slugWithId || slug.endsWith(`-${a.id}`)
      })
      return post
    }
  } catch (error) {
    console.error('Error fetching post:', error)
  }
  return null
}

async function getRelatedPosts(source: string, excludeId: string, limit: number = 3) {
  try {
    const res = await fetch(`${API_URL}/feeds/gossip?limit=20`, {
      next: { revalidate: 600 }
    })
    if (res.ok) {
      const data = await res.json()
      return (data.articles || [])
        .filter((a: any) => a.id.toString() !== excludeId)
        .slice(0, limit)
    }
  } catch (error) {
    console.error('Error fetching related posts:', error)
  }
  return []
}

export async function generateMetadata({ params }: { params: { source: string, slug: string } }): Promise<Metadata> {
  const post = await getPostBySlug(params.source, params.slug)
  
  if (!post) {
    return {
      title: '帖子未找到 | 湾区牛马日常',
    }
  }

  const title = `${post.title || '帖子详情'} | ${params.source} | 湾区牛马日常`
  const description = post.snippet || post.summary || post.title || '热门帖子详情'

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url: `${SITE_METADATA.url}/posts/${params.source}/${params.slug}`,
      siteName: '湾区牛马日常',
      images: post.thumbnail_url ? [post.thumbnail_url] : [SITE_METADATA.ogImage],
      locale: 'zh_CN',
      type: 'article',
      publishedTime: post.published_at,
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: post.thumbnail_url ? [post.thumbnail_url] : [SITE_METADATA.ogImage],
    },
  }
}

export default async function PostDetailPage({ params }: { params: { source: string, slug: string } }) {
  const [post, relatedPosts] = await Promise.all([
    getPostBySlug(params.source, params.slug),
    getRelatedPosts(params.source, '', 3)
  ])

  if (!post) {
    notFound()
  }

  // Filter related posts
  const filteredRelated = relatedPosts.filter((a: any) => a.id.toString() !== post.id.toString()).slice(0, 3)

  // Generate TL;DR bullets
  const snippet = post.snippet || post.summary || post.title || ''
  const bullets = snippet.length > 150 
    ? [
        snippet.substring(0, 150) + '...',
        snippet.substring(150, 300) + (snippet.length > 300 ? '...' : '')
      ].filter(Boolean)
    : [snippet].filter(Boolean)

  // JSON-LD structured data
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: post.title,
    description: post.summary || post.snippet,
    datePublished: post.published_at,
    author: {
      '@type': 'Organization',
      name: post.source || params.source
    },
    publisher: {
      '@type': 'Organization',
      name: '湾区牛马日常'
    },
    image: post.thumbnail_url,
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': post.url
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
          <Link href="/gossip" className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← 返回八卦
          </Link>

          <div className="bg-white rounded-xl shadow-sm p-6 md:p-8">
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">{post.title || '帖子详情'}</h1>
              
              {post.tags && Array.isArray(post.tags) && post.tags.length > 0 && (
                <div className="flex gap-2 mb-4 flex-wrap">
                  {post.tags.map((tag: string, idx: number) => (
                    <span key={idx} className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {post.gossip_score && (
                <div className="mb-4 text-sm text-gray-600">
                  八卦度: {(post.gossip_score * 100).toFixed(0)}%
                </div>
              )}

              <div className="prose max-w-none">
                {bullets.length > 0 && (
                  <div className="mb-6">
                    <h2 className="text-xl font-semibold mb-3">TL;DR</h2>
                    <ul className="list-disc list-inside space-y-2 text-gray-700">
                      {bullets.map((bullet, idx) => (
                        <li key={idx}>{bullet}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {post.summary && (
                  <div className="mb-4">
                    <h2 className="text-xl font-semibold mb-2">摘要</h2>
                    <p className="text-gray-700 whitespace-pre-wrap">{post.summary}</p>
                  </div>
                )}

                {post.snippet && !post.summary && (
                  <div className="mb-4">
                    <p className="text-gray-700">{post.snippet}</p>
                  </div>
                )}

                {post.source && (
                  <div className="mt-6 text-sm text-gray-600">
                    来源: {post.source}
                  </div>
                )}

                {post.url && (
                  <div className="mt-6">
                    <a
                      href={post.url}
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

          {/* Related Posts */}
          {filteredRelated.length > 0 && (
            <div className="mt-8 bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-bold mb-4">更多来自 {params.source}</h2>
              <div className="space-y-3">
                {filteredRelated.map((related: any) => {
                  const relatedSlug = generateSlug(related.title || '')
                  const relatedSlugWithId = `${relatedSlug}-${related.id}`
                  return (
                    <Link
                      key={related.id}
                      href={`/posts/${related.source || 'unknown'}/${relatedSlugWithId}`}
                      className="block p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                    >
                      <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">{related.title}</h3>
                      <p className="text-sm text-gray-600 line-clamp-2">{related.snippet || related.summary}</p>
                      {related.tags && Array.isArray(related.tags) && related.tags.length > 0 && (
                        <div className="flex gap-1 mt-2 flex-wrap">
                          {related.tags.slice(0, 2).map((tag: string, idx: number) => (
                            <span key={idx} className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
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

