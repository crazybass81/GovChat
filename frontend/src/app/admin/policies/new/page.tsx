'use client'

import { useState } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'

export default function NewPolicyPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    agency: '',
    description: '',
    target_audience: '',
    support_type: ''
  })

  if (status === 'loading') {
    return <div className="p-8">로딩 중...</div>
  }

  if (!session || session.user?.email !== 'archt723@gmail.com') {
    router.push('/auth/signin')
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      console.log('새 정책 저장:', formData)
      alert('정책이 성공적으로 저장되었습니다.')
      router.push('/admin/policies')
    } catch (error) {
      console.error('정책 저장 실패:', error)
      alert('정책 저장에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">새 정책 추가</h1>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">정책명 *</label>
              <input
                type="text"
                name="title"
                required
                value={formData.title}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="예: 청년창업지원사업"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">주관기관 *</label>
              <input
                type="text"
                name="agency"
                required
                value={formData.agency}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="예: 중소벤처기업부"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">정책 설명 *</label>
              <textarea
                name="description"
                rows={3}
                required
                value={formData.description}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="정책의 목적과 내용을 설명하세요"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">지원 유형</label>
              <select
                name="support_type"
                value={formData.support_type}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">선택하세요</option>
                <option value="창업지원">창업지원</option>
                <option value="취업지원">취업지원</option>
                <option value="주거지원">주거지원</option>
                <option value="교육지원">교육지원</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">지원 대상</label>
              <input
                type="text"
                name="target_audience"
                value={formData.target_audience}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="예: 청년, 중소기업, 창업자"
              />
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => router.back()}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '저장 중...' : '저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}