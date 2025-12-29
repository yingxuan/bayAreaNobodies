import { Metadata } from 'next'
import Link from 'next/link'
import { SITE_METADATA } from '../../lib/constants'
import { generateSlug } from '../../lib/slug'
import { SUPPORTED_CITIES, formatCityName } from '../../lib/cities'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getCityData(city: string) {
  try {
    const [foodRes, dealsRes, gossipRes] = await Promise.all([
      fetch(`${API_URL}/food/restaurants?cuisine_type=chinese&limit=5`, {
        next: { revalidate: 600 }
      }).catch(() => null),
      fetch(`${API_URL}/feeds/deals?limit=5`, {
        next: { revalidate: 600 }
      }).catch(() => null),
      fetch(`${API_URL}/feeds/gossip?limit=5`, {
        next: { revalidate: 600 }
      }).catch(() => null),
    ])

    const foodData = foodRes?.ok ? await foodRes.json() : null
    const dealsData = dealsRes?.ok ? await dealsRes.json() : null
    const gossipData = gossipRes?.ok ? await gossipRes.json() : null

    return {
      restaurants: foodData?.restaurants || [],
      deals: dealsData?.coupons || [],
      posts: gossipData?.articles || [],
    }
  } catch (error) {
    console.error('Error fetching city data:', error)
    return {
      restaurants: [],
      deals: [],
      posts: [],
    }
  }
}

export async function generateMetadata({ params }: { params: { city: string } }): Promise<Metadata> {
  const cityName = formatCityName(params.city)
  const title = `${cityName} 湾区码农生活指南｜吃什么·羊毛·热帖 | 湾区牛马日常`
  const description = `为在 ${cityName} 的湾区码农老中整理的每日生活与决策信息。`

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      url: `${SITE_METADATA.url}/city/${params.city}`,
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

export default async function CityPage({ params }: { params: { city: string } }) {
  const cityData = await getCityData(params.city)
  const cityName = formatCityName(params.city)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 md:p-8 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {cityName} 湾区码农今日指南
          </h1>
          <p className="text-gray-600">
            为在 {cityName} 的湾区码农老中整理的每日生活与决策信息
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 今日吃什么 */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">🍜 今日吃什么</h2>
              <Link href="/food" className="text-sm text-blue-600 hover:text-blue-800">
                查看更多 →
              </Link>
            </div>
            <div className="space-y-3">
              {cityData.restaurants.slice(0, 5).map((restaurant: any) => {
                const slug = generateSlug(restaurant.name || '')
                const slugWithId = `${slug}-${restaurant.id}`
                return (
                  <Link
                    key={restaurant.id}
                    href={`/eat/${params.city}/${slugWithId}`}
                    className="block p-3 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">{restaurant.name}</h3>
                    <p className="text-sm text-gray-600 line-clamp-1">{restaurant.address}</p>
                    {restaurant.rating && (
                      <p className="text-sm text-yellow-600 mt-1">⭐ {restaurant.rating}</p>
                    )}
                  </Link>
                )
              })}
              {cityData.restaurants.length === 0 && (
                <p className="text-gray-500 text-sm">暂无推荐</p>
              )}
            </div>
          </div>

          {/* 今日羊毛 */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">🛍 今日羊毛</h2>
              <Link href="/deals" className="text-sm text-blue-600 hover:text-blue-800">
                查看更多 →
              </Link>
            </div>
            <div className="space-y-3">
              {cityData.deals.slice(0, 5).map((deal: any) => {
                const slug = generateSlug(deal.title || deal.description || '')
                const slugWithId = `${slug}-${deal.id}`
                return (
                  <Link
                    key={deal.id}
                    href={`/deals/${deal.source || 'unknown'}/${slugWithId}`}
                    className="block p-3 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">{deal.title}</h3>
                    <p className="text-sm text-gray-600 line-clamp-2">{deal.description || deal.snippet}</p>
                    {deal.category && (
                      <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded">
                        {deal.category}
                      </span>
                    )}
                  </Link>
                )
              })}
              {cityData.deals.length === 0 && (
                <p className="text-gray-500 text-sm">暂无新羊毛</p>
              )}
            </div>
          </div>

          {/* 热门帖子 */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">🗣 热门帖子</h2>
              <Link href="/gossip" className="text-sm text-blue-600 hover:text-blue-800">
                查看更多 →
              </Link>
            </div>
            <div className="space-y-3">
              {cityData.posts.slice(0, 5).map((post: any) => {
                const slug = generateSlug(post.title || '')
                const slugWithId = `${slug}-${post.id}`
                return (
                  <Link
                    key={post.id}
                    href={`/posts/${post.source || 'unknown'}/${slugWithId}`}
                    className="block p-3 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">{post.title}</h3>
                    <p className="text-sm text-gray-600 line-clamp-2">{post.snippet || post.summary}</p>
                    {post.tags && Array.isArray(post.tags) && post.tags.length > 0 && (
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {post.tags.slice(0, 1).map((tag: string, idx: number) => (
                          <span key={idx} className="px-2 py-0.5 text-xs bg-purple-50 text-purple-700 rounded">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </Link>
                )
              })}
              {cityData.posts.length === 0 && (
                <p className="text-gray-500 text-sm">暂无热帖</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

