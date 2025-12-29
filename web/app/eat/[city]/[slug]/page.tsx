import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import { SITE_METADATA } from '../../../lib/constants'
import { generateSlug } from '../../../lib/slug'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getRestaurantBySlug(city: string, slug: string) {
  try {
    const res = await fetch(`${API_URL}/food/restaurants?cuisine_type=chinese&limit=100`, {
      next: { revalidate: 600 } // Cache for 10 minutes
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
        const byId = data.restaurants?.find((r: any) => r.id.toString() === extractedId)
        if (byId) return byId
      }
      
      // 3. Find restaurant by matching slug
      const restaurant = data.restaurants?.find((r: any) => {
        const restaurantSlug = generateSlug(r.name || '')
        const slugWithId = `${restaurantSlug}-${r.id}`
        return slug === restaurantSlug || slug === slugWithId || slug.endsWith(`-${r.id}`)
      })
      return restaurant
    }
  } catch (error) {
    console.error('Error fetching restaurant:', error)
  }
  return null
}

async function getRelatedRestaurants(city: string, excludeId: string, limit: number = 3) {
  try {
    const res = await fetch(`${API_URL}/food/restaurants?cuisine_type=chinese&limit=20`, {
      next: { revalidate: 600 }
    })
    if (res.ok) {
      const data = await res.json()
      return (data.restaurants || [])
        .filter((r: any) => r.id.toString() !== excludeId)
        .slice(0, limit)
    }
  } catch (error) {
    console.error('Error fetching related restaurants:', error)
  }
  return []
}

export async function generateMetadata({ params }: { params: { city: string, slug: string } }): Promise<Metadata> {
  const restaurant = await getRestaurantBySlug(params.city, params.slug)
  
  if (!restaurant) {
    return {
      title: '餐厅未找到 | 湾区牛马日常',
    }
  }

  const title = `${restaurant.name} | ${params.city} 美食 | 湾区牛马日常`
  const description = `${restaurant.name} - ${restaurant.address || ''} ${restaurant.rating ? `| ⭐ ${restaurant.rating}` : ''}`

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url: `${SITE_METADATA.url}/eat/${params.city}/${params.slug}`,
      siteName: '湾区牛马日常',
      images: restaurant.photo_url ? [restaurant.photo_url] : [SITE_METADATA.ogImage],
      locale: 'zh_CN',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: restaurant.photo_url ? [restaurant.photo_url] : [SITE_METADATA.ogImage],
    },
  }
}

export default async function RestaurantDetailPage({ params }: { params: { city: string, slug: string } }) {
  const [restaurant, relatedRestaurants] = await Promise.all([
    getRestaurantBySlug(params.city, params.slug),
    getRelatedRestaurants(params.city, '', 3) // Will filter after getting restaurant
  ])

  if (!restaurant) {
    notFound()
  }

  // Filter related restaurants
  const filteredRelated = relatedRestaurants.filter((r: any) => r.id.toString() !== restaurant.id.toString()).slice(0, 3)

  // JSON-LD structured data
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Restaurant',
    name: restaurant.name,
    address: restaurant.address ? {
      '@type': 'PostalAddress',
      streetAddress: restaurant.address
    } : undefined,
    aggregateRating: restaurant.rating && restaurant.user_ratings_total ? {
      '@type': 'AggregateRating',
      ratingValue: restaurant.rating,
      reviewCount: restaurant.user_ratings_total
    } : undefined,
    image: restaurant.photo_url,
    telephone: restaurant.phone,
    priceRange: restaurant.price_level ? '$'.repeat(restaurant.price_level) : undefined,
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link href={`/city/${params.city}`} className="text-blue-600 hover:text-blue-800 mb-4 inline-block">
            ← 返回 {params.city} 指南
          </Link>

          <div className="bg-white rounded-xl shadow-sm p-6 md:p-8">
            <div className="mb-6">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">{restaurant.name}</h1>
              
              {restaurant.photo_url && (
                <img
                  src={restaurant.photo_url}
                  alt={restaurant.name}
                  className="w-full h-64 object-cover rounded-lg mb-4"
                />
              )}

              <div className="space-y-2">
                {restaurant.rating && (
                  <div className="flex items-center gap-2">
                    <span className="text-yellow-600">⭐</span>
                    <span className="font-semibold">{restaurant.rating}</span>
                    {restaurant.user_ratings_total && (
                      <span className="text-gray-600 text-sm">({restaurant.user_ratings_total} 评价)</span>
                    )}
                  </div>
                )}
                
                {restaurant.address && (
                  <div className="text-gray-600">
                    📍 {restaurant.address}
                  </div>
                )}

                {restaurant.phone && (
                  <div className="text-gray-600">
                    📞 {restaurant.phone}
                  </div>
                )}

                {restaurant.price_level && (
                  <div className="text-gray-600">
                    💰 {'$'.repeat(restaurant.price_level)}
                  </div>
                )}

                {restaurant.is_open_now !== null && (
                  <div className={restaurant.is_open_now ? 'text-green-600' : 'text-red-600'}>
                    {restaurant.is_open_now ? '🟢 营业中' : '🔴 已打烊'}
                  </div>
                )}
              </div>
            </div>

            {restaurant.google_maps_url && (
              <div className="mt-6">
                <a
                  href={restaurant.google_maps_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  在 Google Maps 中查看 →
                </a>
              </div>
            )}
          </div>

          {/* Related Restaurants */}
          {filteredRelated.length > 0 && (
            <div className="mt-8 bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-xl font-bold mb-4">更多来自 {params.city}</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {filteredRelated.map((related: any) => {
                  const relatedSlug = generateSlug(related.name || '')
                  const relatedSlugWithId = `${relatedSlug}-${related.id}`
                  return (
                    <Link
                      key={related.id}
                      href={`/eat/${params.city}/${relatedSlugWithId}`}
                      className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                    >
                      {related.photo_url && (
                        <img
                          src={related.photo_url}
                          alt={related.name}
                          className="w-full h-32 object-cover"
                        />
                      )}
                      <div className="p-3">
                        <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">{related.name}</h3>
                        {related.rating && (
                          <p className="text-sm text-gray-600">⭐ {related.rating}</p>
                        )}
                      </div>
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

