'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/lib/stores/authStore'

export default function AdminLoginPage() {
  const [form, setForm] = useState({ email: '', password: '', error: '' })
  const router = useRouter()
  const { login } = useAuthStore()

  const handle = (k: keyof typeof form, v: string) =>
    setForm({ ...form, [k]: v, error: '' })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      // TODO: adminAuthApi.login(form.email, form.password)
      login({ id: form.email, email: form.email, role: 'admin' }, 'mock-token')
      router.replace('/admin/policies')
    } catch {
      handle('error', '로그인 실패: 자격 증명을 확인하세요')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <form
        onSubmit={submit}
        className="w-full max-w-sm bg-surface p-8 rounded-medium shadow space-y-4"
      >
        <h1 className="text-2xl font-semibold text-center">관리자 로그인</h1>

        {form.error && <p className="text-error text-sm">{form.error}</p>}

        <input
          className="border p-2 w-full focus-visible:outline-2 focus-visible:outline-primary"
          placeholder="이메일"
          type="email"
          value={form.email}
          onChange={(e) => handle('email', e.target.value)}
        />
        <input
          className="border p-2 w-full focus-visible:outline-2 focus-visible:outline-primary"
          placeholder="비밀번호"
          type="password"
          value={form.password}
          onChange={(e) => handle('password', e.target.value)}
        />

        <button className="w-full bg-primary text-white py-2 rounded-medium focus-visible:outline-2 focus-visible:outline-primary" type="submit">
          로그인
        </button>

        <div className="flex justify-between text-sm">
          <Link href="/admin/find-id">아이디 찾기</Link>
          <Link href="/admin/reset-password">비밀번호 찾기</Link>
        </div>
      </form>
    </div>
  )
}