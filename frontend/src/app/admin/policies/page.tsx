'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

interface Policy {
  id: string
  title: string
  agency: string
  description: string
  target_audience: string
  created_at: string
  source: 'external' | 'manual'
}

export default function PoliciesPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [policies, setPolicies] = useState<Policy[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (status === 'loading') return
    
    if (!session || session.user?.email !== 'archt723@gmail.com') {
      router.push('/auth/signin')
      return
    }

    fetchPolicies()
  }, [session, status, router])

  const fetchPolicies = async () => {
    try {
      // 임시 데이터 (추후 API 연동)
      const mockPolicies: Policy[] = [
        {
          id: '1',
          title: '청년창업지원사업',
          agency: '중소벤처기업부',
          description: '만 39세 이하 청년의 창업을 지원하는 사업',
          target_audience: '청년, 창업자',
          created_at: '2025-01-14',
          source: 'manual'
        },
        {
          id: '2',
          title: '중소기업 성장지원금',
          agency: '중소기업청',
          description: '중소기업의 성장을 위한 자금 지원',
          target_audience: '중소기업',
          created_at: '2025-01-14',
          source: 'external'
        }
      ]
      
      setPolicies(mockPolicies)
      setLoading(false)
    } catch (error) {
      console.error('정책 목록 조회 실패:', error)
      setLoading(false)
    }
  }

  if (status === 'loading' || loading) {
    return <div className="p-8">로딩 중...</div>
  }

  if (!session || session.user?.email !== 'archt723@gmail.com') {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6 flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">정책 관리</h1>
              <p className="mt-2 text-sm text-gray-600">
                정부 지원사업 정책 데이터 관리
              </p>
            </div>
            <button
              onClick={() => router.push('/admin/policies/new')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              새 정책 추가
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          
          {/* 통계 */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-3 mb-8">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">📋</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        전체 정책
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {policies.length}개
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">🔄</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        외부 수집
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {policies.filter(p => p.source === 'external').length}개
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                      <span className="text-white text-sm font-medium">✏️</span>
                    </div>
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        수동 입력
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {policies.filter(p => p.source === 'manual').length}개
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 정책 목록 */}
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {policies.map((policy) => (
                <li key={policy.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-blue-600 truncate">
                            {policy.title}
                          </p>
                          <div className="ml-2 flex-shrink-0 flex">
                            <p className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              policy.source === 'external' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-purple-100 text-purple-800'
                            }`}>
                              {policy.source === 'external' ? '외부수집' : '수동입력'}
                            </p>
                          </div>
                        </div>
                        <div className="mt-2 sm:flex sm:justify-between">
                          <div className="sm:flex">
                            <p className="flex items-center text-sm text-gray-500">
                              🏢 {policy.agency}
                            </p>
                            <p className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0 sm:ml-6">
                              👥 {policy.target_audience}
                            </p>
                          </div>
                          <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                            <p>
                              {policy.created_at}
                            </p>
                          </div>
                        </div>
                        <div className="mt-2">
                          <p className="text-sm text-gray-600">
                            {policy.description}
                          </p>
                        </div>
                      </div>
                      <div className="ml-4 flex-shrink-0 flex space-x-2">
                        <button
                          onClick={() => router.push(`/admin/policies/${policy.id}`)}
                          className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                        >
                          수정
                        </button>
                        <button
                          onClick={() => {/* 삭제 로직 */}}
                          className="text-red-600 hover:text-red-900 text-sm font-medium"
                        >
                          삭제
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>

        </div>
      </div>
    </div>
  )
}