import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import SessionProvider from '@/components/providers/SessionProvider'
import AuthNavigation from '@/components/AuthNavigation'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'GovChat - 정부지원사업 맞춤 매칭',
  description: '정부지원사업을 맞춤형으로 추천해주는 AI 챗봇',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen flex flex-col bg-gray-50">
        <SessionProvider>
          <Providers>
            <header className="shadow-sm bg-white">
              <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
                <Link href="/" className="text-lg font-bold text-primary">GovChat</Link>
                <nav className="flex gap-6 text-sm items-center">
                  <Link href="/chat" className="hover:text-primary">챗봇</Link>
                  <Link href="/user/search" className="hover:text-primary">사업 검색</Link>
                  <Link href="/user/profile" className="hover:text-primary">내 프로필</Link>
                  <Link href="/admin" className="font-medium hover:text-primary">관리자</Link>
                  <AuthNavigation />
                </nav>
              </div>
            </header>
            <main className="flex-1">{children}</main>
            <footer className="text-center text-xs py-4 text-gray-500">© 2025 GovChat</footer>
          </Providers>
        </SessionProvider>
      </body>
    </html>
  )
}