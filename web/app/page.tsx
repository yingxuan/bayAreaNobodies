'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Main page - redirects to /wealth
export default function Home() {
  const router = useRouter()
  
  useEffect(() => {
    router.replace('/wealth')
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-500">正在跳转...</p>
      </div>
    </div>
  )
}
