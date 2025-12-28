'use client'

export default function TestVideoPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-2xl font-bold mb-4">YouTube Video Embed Test</h1>
      <p className="mb-4">If you can see the video below, the embed code is working correctly.</p>
      
      <div 
        className="mb-4 rounded-lg overflow-hidden" 
        style={{ 
          position: 'relative', 
          paddingBottom: '56.25%', 
          height: 0, 
          backgroundColor: '#000',
          maxWidth: '800px'
        }}
      >
        <iframe
          src="https://www.youtube.com/embed/qmSl1Dptqsw?rel=0"
          title="Test YouTube Video"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          style={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            width: '100%', 
            height: '100%',
            border: 'none'
          }}
        />
      </div>
      
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-2">Test Results:</h2>
        <ul className="list-disc list-inside">
          <li>If you see a black box with YouTube video player → Embed is working ✓</li>
          <li>If you see nothing or an error → There may be a browser/network issue</li>
        </ul>
      </div>
      
      <div className="mt-4">
        <a href="/" className="text-blue-600 hover:underline">← Back to Home</a>
      </div>
    </div>
  )
}

