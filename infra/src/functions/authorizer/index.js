const jwt = require('jsonwebtoken');

/**
 * JWT 토큰을 검증하는 Lambda Authorizer
 * NextAuth.js에서 발급한 JWT 토큰을 검증하여 API Gateway 접근을 제어
 */
exports.handler = async (event) => {
    console.log('Authorizer event:', JSON.stringify(event, null, 2));
    
    try {
        // Authorization 헤더에서 토큰 추출
        const token = extractToken(event);
        
        if (!token) {
            console.log('No token provided');
            return generatePolicy('anonymous', 'Deny', event.methodArn);
        }

        // JWT 토큰 검증
        const decoded = verifyToken(token);
        
        if (!decoded) {
            console.log('Invalid token');
            return generatePolicy('anonymous', 'Deny', event.methodArn);
        }

        console.log('Token verified successfully:', decoded.sub);
        
        // 성공적인 인증 시 Allow 정책 반환
        return generatePolicy(decoded.sub, 'Allow', event.methodArn, {
            email: decoded.email,
            name: decoded.name,
            provider: decoded.provider || 'credentials'
        });

    } catch (error) {
        console.error('Authorizer error:', error);
        return generatePolicy('anonymous', 'Deny', event.methodArn);
    }
};

/**
 * 요청에서 JWT 토큰 추출
 */
function extractToken(event) {
    const authHeader = event.headers?.Authorization || event.headers?.authorization;
    
    if (!authHeader) {
        return null;
    }
    
    // Bearer 토큰 형식 확인
    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
        return null;
    }
    
    return parts[1];
}

/**
 * JWT 토큰 검증
 */
function verifyToken(token) {
    try {
        const secret = process.env.NEXTAUTH_SECRET;
        
        if (!secret) {
            throw new Error('NEXTAUTH_SECRET not configured');
        }
        
        // NextAuth.js JWT 토큰 검증
        const decoded = jwt.verify(token, secret);
        
        // 토큰 만료 확인
        if (decoded.exp && Date.now() >= decoded.exp * 1000) {
            throw new Error('Token expired');
        }
        
        return decoded;
        
    } catch (error) {
        console.error('Token verification failed:', error.message);
        return null;
    }
}

/**
 * API Gateway 정책 생성
 */
function generatePolicy(principalId, effect, resource, context = {}) {
    const policy = {
        principalId: principalId,
        policyDocument: {
            Version: '2012-10-17',
            Statement: [
                {
                    Action: 'execute-api:Invoke',
                    Effect: effect,
                    Resource: resource
                }
            ]
        }
    };
    
    // 컨텍스트 정보 추가 (Lambda 함수에서 사용 가능)
    if (Object.keys(context).length > 0) {
        policy.context = context;
    }
    
    return policy;
}