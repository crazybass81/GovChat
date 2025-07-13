import { verifyToken } from '../jwtHandler.js';
import { logger } from '../logger.js';

export function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ error: '액세스 토큰이 필요합니다.' });
    }

    try {
        const decoded = verifyToken(token);
        req.user = decoded;
        next();
    } catch (error) {
        logger.error('Token verification failed', { error: error.message });
        return res.status(403).json({ error: '유효하지 않은 토큰입니다.' });
    }
}

export function requireAdmin(req, res, next) {
    if (!req.user || req.user.role !== 'admin') {
        logger.warn('Admin access denied', { userId: req.user?.userId });
        return res.status(403).json({ error: '관리자 권한이 필요합니다.' });
    }
    next();
}

export function requireVerified(req, res, next) {
    if (!req.user || !req.user.verified) {
        return res.status(403).json({ error: '실명 인증이 필요합니다.' });
    }
    next();
}

export function rateLimiter(maxRequests = 100, windowMs = 15 * 60 * 1000) {
    const requests = new Map();

    return (req, res, next) => {
        const clientId = req.ip || req.connection.remoteAddress;
        const now = Date.now();
        const windowStart = now - windowMs;

        if (!requests.has(clientId)) {
            requests.set(clientId, []);
        }

        const clientRequests = requests.get(clientId);
        const recentRequests = clientRequests.filter(time => time > windowStart);
        
        if (recentRequests.length >= maxRequests) {
            return res.status(429).json({ 
                error: '요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.' 
            });
        }

        recentRequests.push(now);
        requests.set(clientId, recentRequests);
        next();
    };
}