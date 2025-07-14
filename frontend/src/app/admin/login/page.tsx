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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('') // 기존 오류 메시지 리셋
    try {
      // TODO: 실제 인증 API 연동 또는 Firebase 인증 처리
      // 예: await signInWithEmailAndPassword(auth, email, password);
      // 임시로 성공 처리를 가정
      router.replace('/admin')  // 로그인 성공 시 대시보드로 리디렉트
    } catch (err) {
      // 인증 실패 시 오류 표시
      setError('로그인 실패: 자격 증명을 확인하세요.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleLogin} className="w-full max-w-sm bg-white p-6 rounded shadow-md">
        <h1 className="text-2xl font-bold text-center mb-4">관리자 로그인</h1>
        {/* 이메일 입력 */}
        <Input
          type="email"
          placeholder="이메일"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-3"
          required
        />
        {/* 비밀번호 입력 */}
        <Input
          type="password"
          placeholder="비밀번호"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4"
          required
        />
        {/* 오류 메시지 표시 */}
        {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
        {/* 로그인 버튼 */}
        <Button type="submit" className="w-full">로그인</Button>
      </form>
    </div>
  )
}