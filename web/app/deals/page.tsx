'use client'

import { TabNavigation } from '../components/TabNavigation'
import { DealsTab } from '../components/Tabs'

export default function DealsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <TabNavigation activeTab="deals" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-12">
        <DealsTab />
      </div>
    </div>
  )
}

