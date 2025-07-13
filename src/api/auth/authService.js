import bcrypt from 'bcrypt';
import { generateAccessToken, generateRefreshToken, verifyToken } from '../jwtHandler.js';
import { logger } from '../logger.js';

export class AuthService {
    constructor(dbClient) {
        this.db = dbClient;
    }

    async signup(email, password, name) {
        try {
            const existingUser = await this.db.query(
                'SELECT user_id FROM users WHERE email = $1',
                [email]
            );
            
            if (existingUser.rows.length > 0) {
                throw new Error('이미 존재하는 이메일입니다.');
            }

            const saltRounds = 12;
            const passwordHash = await bcrypt.hash(password, saltRounds);

            const result = await this.db.query(
                'INSERT INTO users (email, password_hash, name) VALUES ($1, $2, $3) RETURNING user_id, email, name, verified, role',
                [email, passwordHash, name]
            );

            const user = result.rows[0];
            
            const accessToken = generateAccessToken({
                userId: user.user_id,
                email: user.email,
                role: user.role
            });
            
            const refreshToken = generateRefreshToken({
                userId: user.user_id
            });

            logger.info('User signup successful', { userId: user.user_id, email });
            
            return {
                user: {
                    id: user.user_id,
                    email: user.email,
                    name: user.name,
                    verified: user.verified,
                    role: user.role
                },
                accessToken,
                refreshToken
            };
        } catch (error) {
            logger.error('Signup failed', { error: error.message, email });
            throw error;
        }
    }

    async login(email, password) {
        try {
            const result = await this.db.query(
                'SELECT user_id, email, password_hash, name, verified, role FROM users WHERE email = $1',
                [email]
            );

            if (result.rows.length === 0) {
                throw new Error('사용자를 찾을 수 없습니다.');
            }

            const user = result.rows[0];
            const isValidPassword = await bcrypt.compare(password, user.password_hash);

            if (!isValidPassword) {
                throw new Error('비밀번호가 올바르지 않습니다.');
            }

            const accessToken = generateAccessToken({
                userId: user.user_id,
                email: user.email,
                role: user.role
            });
            
            const refreshToken = generateRefreshToken({
                userId: user.user_id
            });

            logger.info('User login successful', { userId: user.user_id, email });

            return {
                user: {
                    id: user.user_id,
                    email: user.email,
                    name: user.name,
                    verified: user.verified,
                    role: user.role
                },
                accessToken,
                refreshToken
            };
        } catch (error) {
            logger.error('Login failed', { error: error.message, email });
            throw error;
        }
    }

    async verifyRealName(userId, verificationData) {
        try {
            const isVerified = true; // 실제로는 외부 API 결과

            if (isVerified) {
                await this.db.query(
                    'UPDATE users SET verified = TRUE, last_updated = CURRENT_TIMESTAMP WHERE user_id = $1',
                    [userId]
                );
                
                logger.info('Real name verification successful', { userId });
                return { verified: true };
            } else {
                throw new Error('실명 인증에 실패했습니다.');
            }
        } catch (error) {
            logger.error('Real name verification failed', { error: error.message, userId });
            throw error;
        }
    }

    async getProfile(userId) {
        try {
            const result = await this.db.query(
                'SELECT user_id, email, name, verified, role, created_at FROM users WHERE user_id = $1',
                [userId]
            );

            if (result.rows.length === 0) {
                throw new Error('사용자를 찾을 수 없습니다.');
            }

            return result.rows[0];
        } catch (error) {
            logger.error('Get profile failed', { error: error.message, userId });
            throw error;
        }
    }

    async logout(tokenHash) {
        try {
            await this.db.query(
                'INSERT INTO user_sessions (token_hash, expires_at) VALUES ($1, $2)',
                [tokenHash, new Date(Date.now() + 15 * 60 * 1000)]
            );
            
            logger.info('User logout successful', { tokenHash });
        } catch (error) {
            logger.error('Logout failed', { error: error.message });
            throw error;
        }
    }
}