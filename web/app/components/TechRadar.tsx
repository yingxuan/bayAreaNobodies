import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function formatRelativeTime(isoString: string): string {
  const now = new Date()
  const updated = new Date(isoString)
  const diffMs = now.getTime() - updated.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) {
    return '刚刚'
  } else if (diffMins < 60) {
    return `${diffMins} 分钟前`
  } else {
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) {
      return `${diffHours} 小时前`
    } else {
      const diffDays = Math.floor(diffHours / 24)
      return `${diffDays} 天前`
    }
  }
}

type TechItem = {
  id: string
  title: string
  url: string
  score?: number
  comments?: number
  author?: string
  createdAt?: string
  tags: string[]
  summary?: string
}

type TechTrendingResponse = {
  source: string
  updatedAt: string
  dataSource: 'live' | 'mock'
  items: TechItem[]
}

async function fetchTechTrending(): Promise<TechTrendingResponse> {
  try {
    const res = await fetch(`${API_URL}/tech/trending?source=hn&limit=12`, {
      next: { revalidate: 600 } // 10 minutes cache
    })
    
    if (res.ok) {
      return await res.json()
    }
  } catch (error) {
    console.error('Error fetching tech trending:', error)
  }
  
  // Fallback to empty
  return {
    source: 'hn',
    updatedAt: new Date().toISOString(),
    dataSource: 'mock',
    items: []
  }
}

export async function TechRadar() {
  const data = await fetchTechTrending()
  const top3 = data.items.slice(0, 3)
  const rest = data.items.slice(3, 12)

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">🧠 科技圈新动向</h2>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {data.dataSource === 'mock' && (
            <span className="px-2 py-1 bg-yellow-50 text-yellow-700 rounded" title="使用模拟数据">Mock</span>
          )}
          <span title={new Date(data.updatedAt).toLocaleString('zh-CN')}>
            更新于 {formatRelativeTime(data.updatedAt)}
          </span>
        </div>
      </div>

      {/* Desktop: Top 3 large cards + Right list */}
      <div className="hidden lg:grid lg:grid-cols-3 gap-4">
        {/* Top 3 Large Cards */}
        <div className="lg:col-span-2 space-y-3">
          {top3.map((item) => (
            <a
              key={item.id}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-4 border border-gray-200 rounded-lg hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-gray-900 line-clamp-2 flex-1">{item.title}</h3>
                {item.tags.length > 0 && (
                  <div className="flex gap-1 ml-2 flex-shrink-0">
                    {item.tags.slice(0, 2).map((tag) => (
                      <a
                        key={tag}
                        href={`/tech/tags/${tag}`}
                        onClick={(e) => {
                          e.stopPropagation()
                        }}
                        className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                      >
                        {tag}
                      </a>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-500">
                {item.score !== undefined && (
                  <span>🔥 {item.score}</span>
                )}
                {item.comments !== undefined && (
                  <span>💬 {item.comments}</span>
                )}
                {item.author && (
                  <span>by {item.author}</span>
                )}
              </div>
            </a>
          ))}
        </div>

        {/* Right List */}
        <div className="space-y-2">
          {rest.map((item) => (
            <a
              key={item.id}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block p-3 border border-gray-200 rounded-lg hover:shadow-md transition-all"
            >
              <h4 className="text-sm font-medium text-gray-900 line-clamp-2 mb-1">{item.title}</h4>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                {item.score !== undefined && (
                  <span>🔥 {item.score}</span>
                )}
                {item.comments !== undefined && (
                  <span>💬 {item.comments}</span>
                )}
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* Mobile: Single column cards */}
      <div className="lg:hidden space-y-3">
        {data.items.slice(0, 10).map((item) => (
          <a
            key={item.id}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-4 border border-gray-200 rounded-lg hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-semibold text-gray-900 line-clamp-2 flex-1">{item.title}</h3>
              {item.tags.length > 0 && (
                <div className="flex gap-1 ml-2 flex-shrink-0">
                  {item.tags.slice(0, 2).map((tag) => (
                    <a
                      key={tag}
                      href={`/tech/tags/${tag}`}
                      onClick={(e) => {
                        e.stopPropagation()
                      }}
                      className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                    >
                      {tag}
                    </a>
                  ))}
                </div>
              )}
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              {item.score !== undefined && (
                <span>🔥 {item.score}</span>
              )}
              {item.comments !== undefined && (
                <span>💬 {item.comments}</span>
              )}
              {item.author && (
                <span>by {item.author}</span>
              )}
            </div>
          </a>
        ))}
      </div>

      {/* View More */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <Link
          href="/tech?source=hn"
          className="inline-flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
        >
          查看更多 →
        </Link>
      </div>
    </div>
  )
}

