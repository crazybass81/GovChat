import { NextApiRequest, NextApiResponse } from 'next'
import { serialize } from 'cookie'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
    if (req.method === 'POST') {
        // refreshToken을 서버에서 검증 후 access_token 재발급
        // 실제 구현에서는 refresh_token도 쿠키로 관리
        const newToken = 'new_access_token' // TODO: 실제 토큰 발급 로직
        res.setHeader('Set-Cookie', serialize('access_token', newToken, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            path: '/',
            maxAge: 60 * 60
        }))
        return res.status(200).json({ token: newToken })
    }
    res.status(405).end()
}
