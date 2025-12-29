'use client'

import Link from 'next/link'

export function TabNavigation({ activeTab }: { activeTab: string }) {
  const tabs = [
    { key: 'home', label: '首页', path: '/' },
    { key: 'wealth', label: '暴富', path: '/wealth' },
    { key: 'food', label: '美食', path: '/food' },
    { key: 'deals', label: '羊毛', path: '/deals' },
    { key: 'gossip', label: '八卦', path: '/gossip' }
  ]

  return (
    <>
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-xl font-bold text-gray-900 hover:text-blue-600">
                湾区牛马日常
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="bg-gray-50 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <Link
                key={tab.key}
                href={tab.path}
                className={`py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </>
  )
}

