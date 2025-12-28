'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ArticlePage() {
  const params = useParams()
  const router = useRouter()
  const [article, setArticle] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchArticle()
  }, [params.id])

  const fetchArticle = async () => {
    try {
      const res = await fetch(`${API_URL}/articles/${params.id}`)
      if (res.ok) {
        const data = await res.json()
        setArticle(data)
      } else {
        router.push('/')
      }
    } catch (error) {
      console.error('Error fetching article:', error)
      router.push('/')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  if (!article) return <div className="min-h-screen flex items-center justify-center">Article not found</div>

  const bullets = article.summary_bullets ? JSON.parse(article.summary_bullets) : []
  const tags = article.tags ? JSON.parse(article.tags) : []
  const companies = article.company_tags ? JSON.parse(article.company_tags) : []
  const cities = article.city_hints ? JSON.parse(article.city_hints) : []

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <Link href="/" className="text-xl font-bold text-gray-900">
              湾区牛马日常
            </Link>
            <Link
              href="/"
              className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </nav>

      <article className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-8">
          <h1 className="text-3xl font-bold mb-4">{article.title}</h1>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-6">
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
              {article.source_type}
            </span>
            {article.published_at && (
              <span>{new Date(article.published_at).toLocaleDateString()}</span>
            )}
            <span>Views: {article.views}</span>
            <span>Saves: {article.saves}</span>
          </div>

          {article.summary && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">Summary</h2>
              <p className="text-gray-700 leading-relaxed">{article.summary}</p>
            </div>
          )}

          {bullets.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">Key Points</h2>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {bullets.map((bullet: string, idx: number) => (
                  <li key={idx}>{bullet}</li>
                ))}
              </ul>
            </div>
          )}

          {(tags.length > 0 || companies.length > 0 || cities.length > 0) && (
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">Tags</h2>
              <div className="flex flex-wrap gap-2">
                {companies.map((company: string) => (
                  <span
                    key={company}
                    className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm"
                  >
                    {company}
                  </span>
                ))}
                {cities.map((city: string) => (
                  <span
                    key={city}
                    className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                  >
                    {city}
                  </span>
                ))}
                {tags.map((tag: string) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {article.url && (
            <div className="mt-8 pt-6 border-t">
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Read Original Article →
              </a>
            </div>
          )}
        </div>
      </article>
    </div>
  )
}

