'use client'

import { TabNavigation } from '../components/TabNavigation'
import { FoodTab } from '../components/Tabs'

export default function FoodPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <TabNavigation activeTab="food" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-2 pb-8">
        <FoodTab />
      </div>
    </div>
  )
}

