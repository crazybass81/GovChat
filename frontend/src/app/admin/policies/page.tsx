'use client'

import React from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

interface Policy {
  id: number
  title: string
  category: string
  lastUpdated: string
}

export default function PoliciesPage() {
  // 예시용 정책 데이터 (실제로는 API를 통해 불러옴)
  const policies: Policy[] = [
    { id: 1, title: '청년 취업 지원', category: '고용', lastUpdated: '2025-07-10' },
    { id: 2, title: '소상공인 창업 지원', category: '경제', lastUpdated: '2025-07-08' },
  ]

  const handleDelete = (policyId: number) => {
    // TODO: 정책 삭제 로직 (API 호출 후 상태 갱신)
    alert(`정책 ID ${policyId} 삭제 기능 호출됨`)
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">정책 관리</h2>
      {/* 정책 등록 버튼 */}
      <Link href="/admin/policies/new">
        <Button className="mb-4">+ 새 정책 등록</Button>
      </Link>
      {/* 정책 리스트 테이블 */}
      <table className="min-w-full border-t border-b text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="text-left p-2">정책명</th>
            <th className="text-left p-2">카테고리</th>
            <th className="text-left p-2">최근 수정일</th>
            <th className="p-2">액션</th>
          </tr>
        </thead>
        <tbody>
          {policies.map(policy => (
            <tr key={policy.id} className="border-b hover:bg-gray-50">
              <td className="p-2">{policy.title}</td>
              <td className="p-2">{policy.category}</td>
              <td className="p-2">{policy.lastUpdated}</td>
              <td className="p-2 text-center">
                <Link href={`/admin/policies/${policy.id}/edit`} className="text-blue-600 hover:underline mr-3">
                  수정
                </Link>
                <button onClick={() => handleDelete(policy.id)} className="text-red-600 hover:underline">
                  삭제
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}