/**
 * Place Carousel - (5) 吃点好的 / (6) 肥宅快乐水
 * Google Places restaurants carousel
 */
'use client'

import { useState, useEffect } from 'react'
import { CarouselSection } from './CarouselSection'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type PlaceCardProps = {
  place: {
    id?: number
    place_id?: string
    name: string
    rating?: number
    user_ratings_total?: number
    photo_url?: string
    google_maps_url?: string
    distance_miles?: number
    address?: string
    signature_dish?: string
  }
}

function PlaceCard({ place }: PlaceCardProps) {
  const handleClick = () => {
    if (place.google_maps_url) {
      window.open(place.google_maps_url, '_blank')
    }
  }

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 w-48 bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer"
    >
      {/* Image */}
      <div className="relative w-full h-32 bg-gray-100">
        {place.photo_url ? (
          <img
            src={place.photo_url}
            alt={place.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM2YjcyODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7mlrDpl7s8L3RleHQ+PC9zdmc+'
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            🍽️
          </div>
        )}
      </div>
      
      {/* Content */}
      <div className="p-3">
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-1 mb-1.5">
          {place.name}
        </h4>
        <div className="flex items-center gap-2 text-xs text-gray-600 mb-1">
          {place.rating && (
            <span>⭐ {place.rating.toFixed(1)}</span>
          )}
          {place.user_ratings_total && (
            <span>· {place.user_ratings_total.toLocaleString()} 评论</span>
          )}
          {place.distance_miles && (
            <span>· {place.distance_miles.toFixed(1)} mi</span>
          )}
        </div>
        {place.signature_dish && (
          <div className="text-xs text-orange-600 font-medium">
            🍽️ {place.signature_dish}
          </div>
        )}
      </div>
    </div>
  )
}

type PlaceCarouselProps = {
  title: string
  subtitle?: string
  cuisineType: 'chinese' | 'boba'
  viewMoreHref: string
}

export function PlaceCarousel({ title, subtitle, cuisineType, viewMoreHref }: PlaceCarouselProps) {
  const [places, setPlaces] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPlaces()
  }, [])

  const fetchPlaces = async (shuffle = false) => {
    setLoading(true)
    try {
      // Get user location (fallback to Cupertino)
      let lat = 37.3230
      let lng = -122.0322
      
      if (typeof window !== 'undefined' && navigator.geolocation) {
        try {
          const position = await new Promise<GeolocationPosition>((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 3000 })
          })
          lat = position.coords.latitude
          lng = position.coords.longitude
        } catch (e) {
          // Fallback to Cupertino
        }
      }

      const keyword = cuisineType === 'chinese' ? 'chinese' : 'boba'
      const res = await fetch(`${API_URL}/food/restaurants?cuisine_type=${keyword}&limit=12`).catch(() => null)

      if (res?.ok) {
        const data = await res.json()
        let restaurants = data.restaurants || []
        
        if (shuffle) {
          // Shuffle array
          restaurants = [...restaurants].sort(() => Math.random() - 0.5)
        }
        
        setPlaces(restaurants)
      }
    } catch (error) {
      console.error('Error fetching places:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    fetchPlaces(true)
  }

  if (loading) {
    return (
      <CarouselSection title={title} viewMoreHref={viewMoreHref}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex-shrink-0 w-48 h-40 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </CarouselSection>
    )
  }

  if (places.length === 0) {
    return null
  }

  return (
    <CarouselSection
      title={title}
      viewMoreHref={viewMoreHref}
      onRefresh={handleRefresh}
      showRefresh={true}
    >
      {places.map((place, idx) => (
        <PlaceCard key={place.id || place.place_id || idx} place={place} />
      ))}
    </CarouselSection>
  )
}

