'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type TodayPickData = {
  city: string
  date: string
  restaurant: {
    name: string
    googlePlaceId: string
    googleMapsUrl: string
    rating: number
  }
  dish: {
    name: string
    image: string
  }
  dataSource: 'google_places' | 'mock'
  stale: boolean
  ttlSeconds: number
  updatedAt: string
}

export function TodayEatCard() {
  const [data, setData] = useState<TodayPickData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTodayPick = async () => {
      setLoading(true)
      try {
        const res = await fetch(`${API_URL}/food/today-pick?city=cupertino`, {
          cache: 'no-store',
          headers: {
            'Cache-Control': 'no-cache'
          }
        })
        
        if (res.ok) {
          const result = await res.json()
          setData(result)
        } else {
          console.error('Failed to fetch today pick:', res.status)
        }
      } catch (error) {
        console.error('Error fetching today pick:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTodayPick()
  }, [])

  const handleClick = () => {
    if (data?.restaurant?.googleMapsUrl) {
      window.open(data.restaurant.googleMapsUrl, '_blank')
    }
  }

  if (loading) {
    return (
      <div className="block border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 text-2xl">🍜</div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 text-base mb-1">今天吃什么</h3>
            <p className="text-sm text-gray-600 mb-3">加载中...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="block border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 text-2xl">🍜</div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 text-base mb-1">今天吃什么</h3>
            <p className="text-sm text-gray-600 mb-3">暂无推荐</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      onClick={handleClick}
      className="block border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all cursor-pointer"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 text-2xl">🍜</div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-base mb-2">今天吃什么</h3>
          
          {/* Restaurant Name (Large) */}
          <h4 className="text-lg font-bold text-gray-900 mb-1 line-clamp-1">
            {data.restaurant.name}
          </h4>
          
          {/* Recommended Dish (Bold) */}
          <p className="font-semibold text-gray-700 mb-2">
            {data.dish.name}
          </p>
          
          {/* Dish Image (if available) */}
          {data.dish.image && (
            <div className="mb-2 rounded-lg overflow-hidden">
              <img
                src={data.dish.image}
                alt={data.dish.name}
                className="w-full h-32 object-cover"
                onError={(e) => {
                  // Hide image on error
                  e.currentTarget.style.display = 'none'
                }}
              />
            </div>
          )}
          
          {/* Rating and Location (Small) */}
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
            {data.restaurant.rating > 0 && (
              <span>⭐ {data.restaurant.rating.toFixed(1)}</span>
            )}
            <span>·</span>
            <span className="capitalize">{data.city}</span>
          </div>
          
          {/* Bottom Hint (Small) */}
          <p className="text-xs text-gray-400 mt-2">
            已帮你选好，点开直接导航
          </p>
        </div>
      </div>
    </div>
  )
}

