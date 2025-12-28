'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'trending' | 'coupons'>('trending')

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">湾区牛马日常</h1>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {(['trending', 'coupons'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-8">
          {activeTab === 'trending' && <TrendingTab />}
          {activeTab === 'coupons' && <CouponsTab />}
        </div>
      </div>
    </div>
  )
}


function TrendingTab() {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [source, setSource] = useState<string>('di_li')

  useEffect(() => {
    fetchTrending()
  }, [source])

  const fetchTrending = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (source) params.append('source_type', source)
      const url = `${API_URL}/trending?${params}`
      console.log('Fetching trending from:', url)
      const res = await fetch(url)
      console.log('Response status:', res.status)
      if (res.ok) {
        const data = await res.json()
        console.log('Received data:', data)
        setArticles(data.articles || [])
      } else {
        console.error('API error:', res.status, await res.text())
      }
    } catch (error) {
      console.error('Error fetching trending:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="text-center py-8">Loading trending articles...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4 mb-4">
        <label className="text-sm font-medium">Filter by source:</label>
        <select
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All</option>
          <option value="di_li">1point3acres</option>
          <option value="blind">Teamblind</option>
          <option value="xhs">Xiaohongshu</option>
        </select>
      </div>

      {articles.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No trending articles found. Articles will appear here once background jobs fetch them.
        </div>
      ) : (
        <div className="grid gap-4">
          {articles.map((article) => (
          <Link
            key={article.id}
            href={`/article/${article.id}`}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
          >
            <h3 className="text-lg font-semibold mb-2">{article.title}</h3>
            <p className="text-gray-600 mb-2">{article.summary}</p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>{article.source_type}</span>
              <span>Score: {article.final_score.toFixed(2)}</span>
            </div>
          </Link>
        ))}
        </div>
      )}
    </div>
  )
}


function CouponsTab() {
  const [coupons, setCoupons] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCoupons()
  }, [])

  const fetchCoupons = async () => {
    try {
      const res = await fetch(`${API_URL}/coupons`)
      if (res.ok) {
        const data = await res.json()
        setCoupons(data)
      }
    } catch (error) {
      console.error('Error fetching coupons:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading coupons...</div>

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Coupons</h2>
      <div className="grid gap-4">
        {coupons.map((coupon) => (
          <div key={coupon.id} className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-2">{coupon.title}</h3>
            {coupon.code && (
              <p className="text-blue-600 font-medium mb-2">Code: {coupon.code}</p>
            )}
            {coupon.city && (
              <p className="text-sm text-gray-600 mb-2">Location: {coupon.city}</p>
            )}
            {coupon.terms && (
              <p className="text-sm text-gray-600">{coupon.terms}</p>
            )}
            {coupon.source_url && (
              <a
                href={coupon.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline text-sm"
              >
                View Source
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

