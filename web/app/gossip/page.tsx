'use client'

import { TabNavigation } from '../components/TabNavigation'
import { GossipTab } from '../components/Tabs'

export default function GossipPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <TabNavigation activeTab="gossip" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-2 pb-8">
        <GossipTab />
      </div>
    </div>
  )
}

