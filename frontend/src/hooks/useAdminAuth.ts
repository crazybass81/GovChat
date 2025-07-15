'use client'

import { useSession, signOut } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

const ADMIN_EMAILS = ['admin@govchat.ai', 'archt723@gmail.com']

export function useAdminAuth() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const loading = status === 'loading'
  
  const isAdmin = session?.user?.email && ADMIN_EMAILS.includes(session.user.email)
  const isAuthenticated = !!session && isAdmin

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/admin/login')
    }
  }, [loading, isAuthenticated, router])

  const logout = async () => {
    await signOut({ redirect: false })
    router.push('/admin/login')
  }

  return { isAuthenticated, loading, logout }
}