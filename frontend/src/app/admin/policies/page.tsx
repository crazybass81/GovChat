'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { UrlPolicyModal } from '@/components/admin/UrlPolicyModal'
import { DocumentPolicyModal } from '@/components/admin/DocumentPolicyModal'
import { ApiPolicyModal } from '@/components/admin/ApiPolicyModal'

interface Policy {
  policy_id: string
  title: string
  agency: string
  last_updated: string
  active: boolean
}

interface DiscoveredPolicy {
  id: string
  title: string
  source: string
  url: string
  discovered_at: string
  status: 'pending' | 'approved' | 'rejected'
}

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Policy[]>([])
  const [discoveredPolicies, setDiscoveredPolicies] = useState<DiscoveredPolicy[]>([])
  const [loading, setLoading] = useState(true)
  const [discoveryLoading, setDiscoveryLoading] = useState(true)
  const [pipelineLoading, setPipelineLoading] = useState(false)
  
  // 모달 상태
  const [showUrlModal, setShowUrlModal] = useState(false)
  const [showDocModal, setShowDocModal] = useState(false)
  const [showApiModal, setShowApiModal] = useState(false)

  useEffect(() => {
    fetchPolicies()
    fetchDiscoveredPolicies()
  }, [])

  const fetchPolicies = async () => {
    try {
      const response = await fetch('/api/admin/policies')
      if (response.ok) {
        const data = await response.json()
        setPolicies(data.policies || [])
      }
    } catch (error) {
      console.error('정책 데이터 로드 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchDiscoveredPolicies = async () => {
    try {
      const response = await fetch('/api/admin/policy-discovery')
      if (response.ok) {
        const data = await response.json()
        setDiscoveredPolicies(data.discoveries || [])
      }
    } catch (error) {
      console.error('정책 발굴 데이터 로드 실패:', error)
    } finally {
      setDiscoveryLoading(false)
    }
  }

  const handleDelete = async (policyId: string) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    
    try {
      const response = await fetch(`/api/admin/policies/${policyId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        alert('정책이 삭제되었습니다.')
        fetchPolicies()
      } else {
        alert('삭제에 실패했습니다.')
      }
    } catch (error) {
      alert('오류가 발생했습니다.')
    }
  }

  const handleDataGovLogin = () => {
    window.open('https://auth.data.go.kr/sso/common-login', '_blank')
  }
  
  // 정책 등록 성공 후 처리
  const handlePolicySuccess = () => {
    fetchPolicies()
    alert('정책이 등록되었습니다. 처리가 완료되면 목록에 표시됩니다.')
  }

  const handleDiscoveryAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      const response = await fetch(`/api/admin/policy-discovery/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      })
      
      if (response.ok) {
        fetchDiscoveredPolicies()
      }
    } catch (error) {
      alert('처리 중 오류가 발생했습니다.')
    }
  }

  const handleRunPipeline = async () => {
    setPipelineLoading(true)
    try {
      const response = await fetch('/api/admin/run-pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiId: 'latest' })
      })
      
      const result = await response.json()
      
      if (result.success) {
        alert(`✅ ${result.message}\n\n총 ${result.totalProcessed}개 데이터 처리 완료\n\n` +
          `• ${result.details.apiExtraction}\n` +
          `• ${result.details.webCrawling}\n` +
          `• ${result.details.aiAnalysis}\n` +
          `• ${result.details.dbStorage}\n` +
          `• ${result.details.searchIndex}`)
        fetchPolicies() // 새로 처리된 데이터 로드
      } else {
        alert('❌ 파이프라인 실행 실패: ' + result.error)
      }
    } catch (error) {
      alert('파이프라인 실행 중 오류가 발생했습니다.')
    } finally {
      setPipelineLoading(false)
    }
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">정책 관리</h2>
      {/* 정책 등록 버튼들 */}
      <div className="flex gap-3 mb-6">
        <Button onClick={handleDataGovLogin} className="bg-blue-600 hover:bg-blue-700">
          정책등록(data.go.kr)
        </Button>
        <Button 
          onClick={() => setShowUrlModal(true)} 
          className="bg-blue-500 hover:bg-blue-600"
        >
          정책등록(URL 입력)
        </Button>
        <Button 
          onClick={() => setShowDocModal(true)} 
          className="bg-blue-500 hover:bg-blue-600"
        >
          정책등록(공고문)
        </Button>
        <Button 
          onClick={() => setShowApiModal(true)} 
          className="bg-blue-700 hover:bg-blue-800"
        >
          정책등록(API 정보)
        </Button>
        <Button 
          onClick={handleRunPipeline}
          className="bg-green-600 hover:bg-green-700"
          disabled={pipelineLoading}
        >
          {pipelineLoading ? '파이프라인 실행 중...' : '데이터 파이프라인 실행'}
        </Button>
      </div>
      
      {/* 정책 등록 모달 */}
      <UrlPolicyModal 
        isOpen={showUrlModal} 
        onClose={() => setShowUrlModal(false)} 
        onSuccess={handlePolicySuccess} 
      />
      <DocumentPolicyModal 
        isOpen={showDocModal} 
        onClose={() => setShowDocModal(false)} 
        onSuccess={handlePolicySuccess} 
      />
      <ApiPolicyModal 
        isOpen={showApiModal} 
        onClose={() => setShowApiModal(false)} 
        onSuccess={handlePolicySuccess} 
      />
      {loading ? (
        <div className="text-center py-8">로딩 중...</div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left p-4 font-medium">정책명</th>
                <th className="text-left p-4 font-medium">기관</th>
                <th className="text-left p-4 font-medium">최근 수정일</th>
                <th className="text-left p-4 font-medium">상태</th>
                <th className="p-4 font-medium">액션</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {policies.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-500">
                    등록된 정책이 없습니다.
                  </td>
                </tr>
              ) : (
                policies.map(policy => (
                  <tr key={policy.policy_id} className="hover:bg-gray-50">
                    <td className="p-4">
                      <div className="font-medium">{policy.title}</div>
                    </td>
                    <td className="p-4 text-gray-600">{policy.agency}</td>
                    <td className="p-4 text-gray-600">
                      {new Date(policy.last_updated).toLocaleDateString('ko-KR')}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        policy.active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {policy.active ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex space-x-2">
                        <Link 
                          href={`/admin/policies/${policy.policy_id}`}
                          className="text-blue-600 hover:underline text-sm"
                        >
                          수정
                        </Link>
                        <button 
                          onClick={() => handleDelete(policy.policy_id)}
                          className="text-red-600 hover:underline text-sm"
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
      
      {/* 정책 발굴 섹션 */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-4">정책 발굴 추천</h3>
        {discoveryLoading ? (
          <div className="text-center py-4">발굴 데이터 로딩 중...</div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-4 font-medium">발굴된 정책</th>
                  <th className="text-left p-4 font-medium">출처</th>
                  <th className="text-left p-4 font-medium">발굴일</th>
                  <th className="text-left p-4 font-medium">상태</th>
                  <th className="p-4 font-medium">액션</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {discoveredPolicies.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-8 text-gray-500">
                      발굴된 정책이 없습니다.
                    </td>
                  </tr>
                ) : (
                  discoveredPolicies.map(policy => (
                    <tr key={policy.id} className="hover:bg-gray-50">
                      <td className="p-4">
                        <div className="font-medium">{policy.title}</div>
                        <a href={policy.url} target="_blank" rel="noopener noreferrer" 
                           className="text-blue-600 hover:underline text-sm">
                          링크 확인 →
                        </a>
                      </td>
                      <td className="p-4 text-gray-600">{policy.source}</td>
                      <td className="p-4 text-gray-600">
                        {new Date(policy.discovered_at).toLocaleDateString('ko-KR')}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          policy.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          policy.status === 'approved' ? 'bg-green-100 text-green-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {policy.status === 'pending' ? '대기' :
                           policy.status === 'approved' ? '승인' : '거부'}
                        </span>
                      </td>
                      <td className="p-4">
                        {policy.status === 'pending' && (
                          <div className="flex space-x-2">
                            <button 
                              onClick={() => handleDiscoveryAction(policy.id, 'approve')}
                              className="text-green-600 hover:underline text-sm"
                            >
                              승인
                            </button>
                            <button 
                              onClick={() => handleDiscoveryAction(policy.id, 'reject')}
                              className="text-red-600 hover:underline text-sm"
                            >
                              거부
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}