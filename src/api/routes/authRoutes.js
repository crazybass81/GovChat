import express from 'express';
import { AuthService } from '../auth/authService.js';
import { authenticateToken, rateLimiter } from '../middleware/authMiddleware.js';
import { logger } from '../logger.js';

const router = express.Router();
const authRateLimit = rateLimiter(10, 15 * 60 * 1000);

export function createAuthRoutes(dbClient) {
    const authService = new AuthService(dbClient);

    router.post('/signup', authRateLimit, async (req, res) => {
        try {
            const { email, password, name } = req.body;

            if (!email || !password || !name) {
                return res.status(400).json({ 
                    error: '이메일, 비밀번호, 이름은 필수 입력 사항입니다.' 
                });
            }

            const result = await authService.signup(email, password, name);
            
            res.status(201).json({
                message: '회원가입이 완료되었습니다.',
                user: result.user,
                accessToken: result.accessToken,
                refreshToken: result.refreshToken
            });
        } catch (error) {
            logger.error('Signup endpoint error', { error: error.message });
            res.status(400).json({ error: error.message });
        }
    });

    router.post('/login', authRateLimit, async (req, res) => {
        try {
            const { email, password } = req.body;

            if (!email || !password) {
                return res.status(400).json({ 
                    error: '이메일과 비밀번호를 입력해주세요.' 
                });
            }

            const result = await authService.login(email, password);
            
            res.json({
                message: '로그인이 완료되었습니다.',
                user: result.user,
                accessToken: result.accessToken,
                refreshToken: result.refreshToken
            });
        } catch (error) {
            logger.error('Login endpoint error', { error: error.message });
            res.status(401).json({ error: error.message });
        }
    });

    router.get('/profile', authenticateToken, async (req, res) => {
        try {
            const profile = await authService.getProfile(req.user.userId);
            res.json({ user: profile });
        } catch (error) {
            logger.error('Profile endpoint error', { error: error.message });
            res.status(404).json({ error: error.message });
        }
    });

    router.post('/verify-realname', authenticateToken, async (req, res) => {
        try {
            const { verificationData } = req.body;
            const result = await authService.verifyRealName(req.user.userId, verificationData);
            
            res.json({
                message: '실명 인증이 완료되었습니다.',
                verified: result.verified
            });
        } catch (error) {
            logger.error('Real name verification endpoint error', { error: error.message });
            res.status(400).json({ error: error.message });
        }
    });

    router.post('/logout', authenticateToken, async (req, res) => {
        try {
            const token = req.headers['authorization']?.split(' ')[1];
            if (token) {
                await authService.logout(token);
            }
            
            res.json({ message: '로그아웃이 완료되었습니다.' });
        } catch (error) {
            logger.error('Logout endpoint error', { error: error.message });
            res.status(500).json({ error: '로그아웃 처리 중 오류가 발생했습니다.' });
        }
    });

    return router;
}