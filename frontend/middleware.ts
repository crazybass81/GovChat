import { withAuth } from 'next-auth/middleware'

export default withAuth(
  function middleware(req) {
    // 관리자 페이지 접근 시에만 인증 체크
  },
  {
    callbacks: {
      authorized: ({ token, req }) => {
        // 관리자 페이지가 아니면 항상 허용
        if (!req.nextUrl.pathname.startsWith('/admin')) {
          return true
        }
        
        // 관리자 로그인 페이지는 허용
        if (req.nextUrl.pathname === '/admin/login') {
          return true
        }
        
        // 관리자 페이지는 인증된 관리자만 허용
        const adminEmails = ['admin@govchat.ai', 'archt723@gmail.com']
        return !!token && adminEmails.includes(token.email as string)
      },
    },
  }
)

export const config = {
  matcher: ['/admin/:path*']
}