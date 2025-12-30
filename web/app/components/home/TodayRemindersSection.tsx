/**
 * Today Reminders Section - Wrapper for TodayAlertBar in CollapsibleSection
 */
'use client'

import { TodayAlertBar } from '../TodayAlertBar'

export function TodayRemindersSection() {
  return (
    <div className="py-2">
      <TodayAlertBar />
    </div>
  )
}

