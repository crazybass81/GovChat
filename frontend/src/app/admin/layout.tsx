import React, { ReactNode } from 'react'
import Link from 'next/link'

interface AdminLayoutProps {
    children: ReactNode
}

export default function AdminLayout({ children }: AdminLayoutProps) {
    return (
        <div className="min-h-screen flex">
            {/* 사이드바 메뉴 */}
            <aside className="w-60 bg-gray-100 p-4">
                <h2 className="text-xl font-bold text-center mb-6">GovChat Admin</h2>
                <nav className="space-y-2">
                    <Link href="/admin" className="block px-3 py-2 rounded hover:bg-gray-200">
                        대시보드
                    </Link>
                    <Link href="/admin/policies" className="block px-3 py-2 rounded hover:bg-gray-200">
                        정책 관리
                    </Link>
                    <Link href="/admin/users" className="block px-3 py-2 rounded hover:bg-gray-200">
                        사용자 목록
                    </Link>
                </nav>
            </aside>
            {/* 메인 콘텐츠 영역 */}
            <main className="flex-1 p-6 bg-gray-50">
                {children}
            </main>
        </div>
    )
}