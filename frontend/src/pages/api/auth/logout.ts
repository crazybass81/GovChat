import { NextApiRequest, NextApiResponse } from 'next'
import { serialize } from 'cookie'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
    if (req.method === 'POST') {
        // 로그아웃 시 토큰 쿠키 삭제
        res.setHeader('Set-Cookie', serialize('access_token', '', {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            path: '/',
            maxAge: 0
        }))
        return res.status(200).json({ ok: true })
    }
    res.status(405).end()
}
