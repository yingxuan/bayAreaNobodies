/**
 * Place Grid - 2x2 grid for restaurants/boba
 * Replaces carousel with a compact grid layout
 */
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

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
    price_level?: number
  }
}

function PlaceCard({ place }: PlaceCardProps) {
  const handleClick = () => {
    if (place.google_maps_url) {
      window.open(place.google_maps_url, '_blank')
    }
  }

  // Always show meta row with placeholders if missing
  const hasRating = place.rating !== undefined && place.rating !== null
  const hasDistance = place.distance_miles !== undefined && place.distance_miles !== null
  const hasPrice = place.price_level !== undefined && place.price_level !== null

  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-all cursor-pointer flex flex-col h-full min-h-[220px]"
    >
      {/* Image - Fixed aspect ratio container */}
      <div className="relative w-full aspect-[4/3] bg-gray-100 flex-shrink-0 overflow-hidden">
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
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-2xl">
            🍽️
          </div>
        )}
      </div>
      
      {/* Content - Fixed structure with consistent spacing */}
      <div className="p-3 flex flex-col flex-1 min-h-0">
        {/* Name - Standardized to line-clamp-1 for consistency */}
        <h4 className="text-sm font-semibold text-gray-900 line-clamp-1 mb-1.5 flex-shrink-0">
          {place.name}
        </h4>
        
        {/* Meta row: rating + distance - ALWAYS present with placeholders */}
        <div className="flex items-center gap-1.5 text-xs text-gray-600 mb-1 flex-shrink-0 h-4">
          {hasRating ? (
            <span className="flex items-center gap-0.5">
              <span>⭐</span>
              <span className="font-medium">{place.rating!.toFixed(1)}</span>
            </span>
          ) : (
            <span className="text-gray-400">—</span>
          )}
          <span className="text-gray-400">·</span>
          {hasDistance ? (
            <span>{place.distance_miles!.toFixed(1)} mi</span>
          ) : (
            <span className="text-gray-400">—</span>
          )}
        </div>
        
        {/* Price row - Always reserve space (invisible placeholder if missing) */}
        <div className="text-xs text-gray-500 mt-auto flex-shrink-0 h-4">
          {hasPrice ? (
            <span>{'$'.repeat(place.price_level!)}</span>
          ) : (
            <span className="opacity-0">$</span>
          )}
        </div>
      </div>
    </div>
  )
}

type PlaceGridProps = {
  title: string
  cuisineType: 'chinese' | 'boba'
  viewMoreHref?: string
}

export function PlaceGrid({ title, cuisineType, viewMoreHref }: PlaceGridProps) {
  const [places, setPlaces] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPlaces()
  }, [cuisineType])

  const fetchPlaces = async () => {
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
        // Sort by rating/reviewCount (existing ranking) and take top 4
        const restaurants = (data.restaurants || [])
          .sort((a: any, b: any) => {
            // Sort by rating first, then by review count
            const ratingA = a.rating || 0
            const ratingB = b.rating || 0
            if (ratingB !== ratingA) {
              return ratingB - ratingA
            }
            const reviewsA = a.user_ratings_total || 0
            const reviewsB = b.user_ratings_total || 0
            return reviewsB - reviewsA
          })
          .slice(0, 4) // Exactly 4 items for homepage
        setPlaces(restaurants)
      }
    } catch (error) {
      console.error('Error fetching places:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-bold text-gray-900">{title}</h3>
          {viewMoreHref && (
            <Link href={viewMoreHref} className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap flex-shrink-0">
              更多 →
            </Link>
          )}
        </div>
        
        {/* Loading grid */}
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-gray-100 rounded-lg aspect-[4/3] animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (places.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3 flex-shrink-0">
        <h3 className="text-base font-bold text-gray-900">{title}</h3>
        {viewMoreHref && (
          <Link href={viewMoreHref} className="text-xs text-blue-600 hover:text-blue-700 whitespace-nowrap flex-shrink-0">
            更多 →
          </Link>
        )}
      </div>
      
      {/* 2x2 Grid - items-stretch ensures equal heights */}
      <div className="grid grid-cols-2 gap-3 items-stretch">
        {places.map((place, idx) => (
          <PlaceCard key={place.id || place.place_id || idx} place={place} />
        ))}
      </div>
    </div>
  )
}

