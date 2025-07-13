'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function SignupPage() {
  const [form, setForm] = useState({
    name: '',
    phone: '',
    email: '',
    password: '',
    confirm: '',
    error: '',
  })
  const router = useRouter()

  const handle = (k: keyof typeof form, v: string) =>
    setForm({ ...form, [k]: v, error: '' })

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (form.password !== form.confirm) {
      handle('error', '비밀번호가 일치하지 않습니다')
      return
    }
    try {
      // TODO: userAuthApi.signup({
      //   name: form.name,
      //   phone: form.phone,
      //   email: form.email,
      //   password: form.password,
      // })
      router.replace('/user/login?signup=success')
    } catch {
      handle('error', '회원가입에 실패했습니다')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <form
        onSubmit={submit}
        className="w-full max-w-sm bg-surface p-8 rounded-medium shadow space-y-4"
      >
        <h1 className="text-2xl font-semibold text-center">회원가입</h1>

        {form.error && <p className="text-error text-sm">{form.error}</p>}

        <input 
          className="border p-2 w-full focus-visible:outline-2 focus-visible:outline-primary" 
          placeholder="이름" 
          value={form.name}
          onChange={(e) => handle('name', e.target.value)} 
        />
        <input 
          className="border p-2 w-full focus-visible:outline-2 focus-visible:outline-primary" 
          placeholder="휴대폰번호(- 없이)"
          value={form.phone} 
          onChange={(e) => handle('phone', e.target.value)} 
        />
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
        <input 
          className="border p-2 w-full focus-visible:outline-2 focus-visible:outline-primary" 
          placeholder="비밀번호 확인" 
          type="password"
          value={form.confirm} 
          onChange={(e) => handle('confirm', e.target.value)} 
        />

        <button className="w-full bg-primary text-white py-2 rounded-medium focus-visible:outline-2 focus-visible:outline-primary">
          가입하기
        </button>
      </form>
    </div>
  )
}