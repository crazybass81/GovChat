'use client'

import React from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

export default function AdminDashboardPage() {
  // 예시 지표 데이터 (실제로는 API를 통해 불러옴)
  const stats = {
    totalPolicies: 12,
    totalUsers: 134,
    matchSuccessRate: 87  // 퍼센트(%)
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">대시보드</h2>
      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>총 정책 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.totalPolicies}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>총 사용자 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.totalUsers}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>매칭 성공률</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.matchSuccessRate}%</p>
          </CardContent>
        </Card>
      </div>

      {/* 차트 섹션 */}
      <div className="mt-8 bg-white p-4 rounded shadow">
        <h3 className="text-lg font-semibold mb-4">월별 매칭 성공률 추이</h3>
        <p className="text-sm text-gray-500">[차트 예시: 월별 매칭 성공률 Chart]</p>
      </div>
    </div>
  )
}