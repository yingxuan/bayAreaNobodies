import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center max-w-md px-4">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
        <p className="text-xl text-gray-600 mb-8">页面未找到</p>
        <div className="space-y-4">
          <Link
            href="/"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            返回首页
          </Link>
          <div className="text-sm text-gray-500">
            <p className="mb-2">或者浏览：</p>
            <div className="flex gap-4 justify-center">
              <Link href="/wealth" className="text-blue-600 hover:text-blue-800">暴富</Link>
              <Link href="/food" className="text-blue-600 hover:text-blue-800">美食</Link>
              <Link href="/deals" className="text-blue-600 hover:text-blue-800">羊毛</Link>
              <Link href="/gossip" className="text-blue-600 hover:text-blue-800">八卦</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

