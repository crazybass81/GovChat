'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

export default function AdminLoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // API 호출로 인증
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/admin/auth`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password })
      })
      
      const data = await response.json()
      
      if (data.success) {
        localStorage.setItem('admin_session', 'true')
        localStorage.setItem('admin_email', email)
        localStorage.setItem('admin_token', data.token)
        router.replace('/admin')
      } else {
        setError(data.message || '로그인에 실패했습니다.')
      }
    } catch (err) {
      // 백엔드 API가 없으면 임시 로직 사용
      if (email === 'archt723@gmail.com' && password === '1q2w3e2w1q!') {
        localStorage.setItem('admin_session', 'true')
        localStorage.setItem('admin_email', email)
        router.replace('/admin')
      } else {
        setError('이메일 또는 비밀번호가 올바르지 않습니다.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleLogin} className="w-full max-w-sm bg-white p-6 rounded shadow-md">
        <h1 className="text-2xl font-bold text-center mb-4">관리자 로그인</h1>
        
        <Input
          type="email"
          placeholder="이메일"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-3"
          required
        />
        
        <Input
          type="password"
          placeholder="비밀번호"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4"
          required
        />
        
        {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
        
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? '로그인 중...' : '로그인'}
        </Button>
        
        <div className="mt-4 text-xs text-gray-500 text-center">
          관리자 계정: archt723@gmail.com
        </div>
      </form>
    </div>
  )
}