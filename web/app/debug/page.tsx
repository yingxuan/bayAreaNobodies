'use client'

import { useEffect, useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function DebugPage() {
  const [status, setStatus] = useState<string>('Initializing...')
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    console.log('[Debug] Component mounted')
    setStatus('Fetching...')
    
    fetch(`${API_URL}/feeds/food?limit=1`)
      .then(res => {
        console.log('[Debug] Response status:', res.status)
        setStatus(`Response: ${res.status}`)
        return res.json()
      })
      .then(data => {
        console.log('[Debug] Data received:', data)
        setData(data)
        setStatus(`Success: ${data.articles?.length || 0} articles`)
      })
      .catch(error => {
        console.error('[Debug] Error:', error)
        setStatus(`Error: ${error.message}`)
      })
  }, [])

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-2xl font-bold mb-4">Debug Page</h1>
      
      <div className="bg-white p-4 rounded shadow mb-4">
        <h2 className="font-semibold mb-2">Status:</h2>
        <p>{status}</p>
        <p className="text-sm text-gray-500 mt-2">API URL: {API_URL}</p>
      </div>

      {data && (
        <div className="bg-white p-4 rounded shadow">
          <h2 className="font-semibold mb-2">Data:</h2>
          <pre className="text-xs overflow-auto bg-gray-100 p-2 rounded">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}

      <div className="mt-4">
        <a href="/" className="text-blue-600 hover:underline">← Back to Home</a>
      </div>
    </div>
  )
}

