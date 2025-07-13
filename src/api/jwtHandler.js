import jwt from 'jsonwebtoken';

// JWT 토큰을 서명하고 검증하는 데 사용되는 비밀 키
const secretKey = process.env.JWT_SECRET || 'defaultSecret';

// 15분 동안 유효한 액세스 토큰을 생성하는 함수
export function generateAccessToken(payload) {
    // payload는 토큰에 포함될 사용자 정보나 데이터입니다.
    return jwt.sign(payload, secretKey, { expiresIn: '15m' });
}

// 7일 동안 유효한 리프레시 토큰을 생성하는 함수
export function generateRefreshToken(payload) {
    // payload는 토큰에 포함될 사용자 정보나 데이터입니다.
    return jwt.sign(payload, secretKey, { expiresIn: '7d' });
}

// 주어진 JWT 토큰의 유효성을 검증하는 함수
export function verifyToken(token) {
    try {
        // 토큰이 유효한 경우 디코딩된 데이터를 반환합니다.
        return jwt.verify(token, secretKey);
    } catch (error) {
        // 토큰이 유효하지 않거나 만료된 경우 오류를 발생시킵니다.
        throw new Error('Invalid token');
    }
}