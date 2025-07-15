'use client'

import React, { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

interface DashboardStats {
  totalPolicies: number
  totalUsers: number
  totalMatches: number
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalPolicies: 0,
    totalUsers: 0,
    totalMatches: 0
  })
  const [recentStats, setRecentStats] = useState({
    today: 0,
    thisWeek: 0,
    thisMonth: 0
  })
  const [matchStats, setMatchStats] = useState({
    today: 0,
    thisWeek: 0,
    thisMonth: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [statsResponse, recentResponse, matchResponse] = await Promise.all([
          fetch('/api/admin/stats'),
          fetch('/api/admin/recent-users'),
          fetch('/api/admin/recent-matches')
        ])
        
        if (statsResponse.ok) {
          const data = await statsResponse.json()
          setStats(data)
        }
        
        if (recentResponse.ok) {
          const recentData = await recentResponse.json()
          setRecentStats(recentData)
        }
        
        if (matchResponse.ok) {
          const matchData = await matchResponse.json()
          setMatchStats(matchData)
        }
      } catch (error) {
        console.error('통계 데이터 로드 실패:', error)
        setStats({
          totalPolicies: 0,
          totalUsers: 0,
          totalMatches: 0
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">대시보드</h2>
      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>정책 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-600">
              {loading ? '...' : stats.totalPolicies.toLocaleString()}
            </p>
            <p className="text-sm text-gray-500 mt-1">등록된 정책</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>사용자 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-600">
              {loading ? '...' : stats.totalUsers.toLocaleString()}
            </p>
            <p className="text-sm text-gray-500 mt-1">가입 사용자</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>매칭 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-600">
              {loading ? '...' : stats.totalMatches.toLocaleString()}
            </p>
            <p className="text-sm text-gray-500 mt-1">성공한 매칭</p>
          </CardContent>
        </Card>
      </div>

      {/* 최근 활동 섹션 */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">최근 가입자 수</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">오늘</span>
              <span className="font-medium">+{recentStats.today}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">이번 주</span>
              <span className="font-medium">+{recentStats.thisWeek}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">이번 달</span>
              <span className="font-medium">+{recentStats.thisMonth}</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">최근 매칭 수</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">오늘</span>
              <span className="font-medium">+{matchStats.today}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">이번 주</span>
              <span className="font-medium">+{matchStats.thisWeek}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">이번 달</span>
              <span className="font-medium">+{matchStats.thisMonth}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}