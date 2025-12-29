import { Metadata } from 'next'
import { RiskPageContent } from '../components/RiskPageContent'
import { SITE_METADATA } from '../lib/constants'

export const metadata: Metadata = {
  title: '今日提醒 | 湾区牛马日常',
  description: '湾区码农今天应该注意什么 - 报税、合规、工作、生活提醒',
}

export default function RiskPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl shadow-sm p-6 md:p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">⚠️ 今日提醒</h1>
          <p className="text-sm text-gray-500 mb-6">
            湾区码农今天应该注意什么 - 如果不知道，可能会吃亏
          </p>
          
          <RiskPageContent />
          
          {/* Disclaimer */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              信息仅供参考，不构成法律/投资建议
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

