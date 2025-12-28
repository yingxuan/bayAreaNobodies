'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface User {
  id: number
  email: string
  preferred_city: string | null
}

export default function Home() {
  const [user, setUser] = useState<User | null>(null)
  const [activeTab, setActiveTab] = useState<'digest' | 'trending' | 'portfolio' | 'coupons'>('digest')
  const router = useRouter()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const res = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) {
        const userData = await res.json()
        setUser(userData)
      } else {
        router.push('/login')
      }
    } catch (error) {
      router.push('/login')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    router.push('/login')
  }

  if (!user) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">湾区牛马日常</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">{user.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {(['digest', 'trending', 'portfolio', 'coupons'] as const).map((tab) => (
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
          {activeTab === 'digest' && <DigestTab user={user} />}
          {activeTab === 'trending' && <TrendingTab />}
          {activeTab === 'portfolio' && <PortfolioTab />}
          {activeTab === 'coupons' && <CouponsTab city={user.preferred_city} />}
        </div>
      </div>
    </div>
  )
}

function DigestTab({ user }: { user: User }) {
  const [digest, setDigest] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDigest()
  }, [])

  const fetchDigest = async () => {
    const token = localStorage.getItem('token')
    try {
      const res = await fetch(`${API_URL}/digests/today`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setDigest(JSON.parse(data.content_json))
      }
    } catch (error) {
      console.error('Error fetching digest:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading digest...</div>
  if (!digest) return <div>No digest available for today</div>

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Today's Digest</h2>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Portfolio Summary</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Total Value</p>
            <p className="text-2xl font-bold">${digest.portfolio?.total_value?.toFixed(2) || '0.00'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">P&L</p>
            <p className={`text-2xl font-bold ${(digest.portfolio?.total_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              ${digest.portfolio?.total_pnl?.toFixed(2) || '0.00'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Trending</h3>
        <div className="space-y-4">
          {Object.entries(digest.trending || {}).map(([source, items]: [string, any]) => (
            <div key={source}>
              <h4 className="font-medium text-gray-700 mb-2">{source}</h4>
              <div className="space-y-2">
                {items.map((item: any) => (
                  <Link
                    key={item.id}
                    href={`/article/${item.id}`}
                    className="block p-3 bg-gray-50 rounded hover:bg-gray-100"
                  >
                    <p className="font-medium">{item.title}</p>
                    <p className="text-sm text-gray-600">{item.summary}</p>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Coupons</h3>
        <div className="space-y-2">
          {digest.coupons?.map((coupon: any) => (
            <div key={coupon.id} className="p-3 bg-gray-50 rounded">
              <p className="font-medium">{coupon.title}</p>
              {coupon.code && <p className="text-sm text-blue-600">Code: {coupon.code}</p>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function TrendingTab() {
  const [articles, setArticles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [source, setSource] = useState<string>('')

  useEffect(() => {
    fetchTrending()
  }, [source])

  const fetchTrending = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (source) params.append('source_type', source)
      const res = await fetch(`${API_URL}/trending?${params}`)
      if (res.ok) {
        const data = await res.json()
        setArticles(data.articles || [])
      }
    } catch (error) {
      console.error('Error fetching trending:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Loading trending articles...</div>

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
    </div>
  )
}

function PortfolioTab() {
  const router = useRouter()
  const [holdings, setHoldings] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({ ticker: '', quantity: '', cost_basis: '', tags: '' })

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const [holdingsRes, summaryRes] = await Promise.all([
        fetch(`${API_URL}/holdings`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/portfolio/summary`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ])

      if (holdingsRes.ok) {
        const holdingsData = await holdingsRes.json()
        setHoldings(holdingsData)
      }

      if (summaryRes.ok) {
        const summaryData = await summaryRes.json()
        setSummary(summaryData)
      }
    } catch (error) {
      console.error('Error fetching portfolio:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault()
    const token = localStorage.getItem('token')
    try {
      const res = await fetch(`${API_URL}/holdings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ticker: formData.ticker,
          quantity: parseFloat(formData.quantity),
          cost_basis: parseFloat(formData.cost_basis),
          tags: formData.tags || null
        })
      })
      if (res.ok) {
        setShowAddForm(false)
        setFormData({ ticker: '', quantity: '', cost_basis: '', tags: '' })
        fetchData()
      }
    } catch (error) {
      console.error('Error adding holding:', error)
    }
  }

  if (loading) return <div>Loading portfolio...</div>

  return (
    <div className="space-y-6">
      {summary && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Portfolio Summary</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Total Value</p>
              <p className="text-2xl font-bold">${summary.total_value.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">P&L</p>
              <p className={`text-2xl font-bold ${summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${summary.total_pnl.toFixed(2)} ({summary.total_pnl_percent.toFixed(2)}%)
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Holdings</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Add Holding
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleAdd} className="bg-white rounded-lg shadow p-6 space-y-4">
          <input
            type="text"
            placeholder="Ticker (e.g., NVDA)"
            value={formData.ticker}
            onChange={(e) => setFormData({ ...formData, ticker: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          />
          <input
            type="number"
            step="0.01"
            placeholder="Quantity"
            value={formData.quantity}
            onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          />
          <input
            type="number"
            step="0.01"
            placeholder="Cost Basis"
            value={formData.cost_basis}
            onChange={(e) => setFormData({ ...formData, cost_basis: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
            required
          />
          <input
            type="text"
            placeholder="Tags (optional)"
            value={formData.tags}
            onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <div className="flex space-x-2">
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Add
            </button>
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ticker</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost Basis</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">P&L</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {summary?.holdings?.map((holding: any) => (
              <tr key={holding.ticker}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{holding.ticker}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{holding.quantity}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">${holding.cost_basis.toFixed(2)}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">${holding.value?.toFixed(2) || 'N/A'}</td>
                <td className={`px-6 py-4 whitespace-nowrap text-sm ${holding.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${holding.pnl?.toFixed(2) || '0.00'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function CouponsTab({ city }: { city: string | null }) {
  const [coupons, setCoupons] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchCoupons()
  }, [city])

  const fetchCoupons = async () => {
    try {
      const params = new URLSearchParams()
      if (city) params.append('city', city)
      const res = await fetch(`${API_URL}/coupons?${params}`)
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

