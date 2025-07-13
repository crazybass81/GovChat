import { NextApiRequest, NextApiResponse } from 'next'
import { serialize } from 'cookie'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
    if (req.method === 'POST') {
        // 로그인 시 토큰을 HTTP-Only 쿠키로 저장
        const { token } = req.body
        if (!token) return res.status(400).json({ error: 'Token required' })
        res.setHeader('Set-Cookie', serialize('access_token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            path: '/',
            maxAge: 60 * 60 // 1시간
        }))
        return res.status(200).json({ ok: true })
    }
    res.status(405).end()
}
