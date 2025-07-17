'use client'

import { useSession, signOut } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export function useAdminAuth() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const loading = status === 'loading'
  
  const isAdmin = session?.user?.role === 'admin' || session?.user?.role === 'master'
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