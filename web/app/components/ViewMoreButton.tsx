'use client'

import Link from 'next/link'

interface ViewMoreButtonProps {
  href: string
  text?: string
}

export function ViewMoreButton({ href, text = '查看更多' }: ViewMoreButtonProps) {
  return (
    <Link
      href={href}
      className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
    >
      {text} →
    </Link>
  )
}

