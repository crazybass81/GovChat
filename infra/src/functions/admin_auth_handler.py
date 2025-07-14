"""
관리자 인증 핸들러
"""

import json
import hashlib
import hmac
from aws_lambda_powertools import Logger

logger = Logger()

# 관리자 계정 (실제로는 DynamoDB나 환경변수에 저장)
ADMIN_ACCOUNTS = {
    'archt723@gmail.com': {
        'password_hash': 'hashed_password_here',  # 실제로는 해시된 비밀번호
        'role': 'admin'
    }
}

def handler(event, context):
    """관리자 로그인 처리"""
    try:
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '')
        password = body.get('password', '')
        
        # 간단한 검증 (실제로는 해시 비교)
        if email == 'archt723@gmail.com' and password == '1q2w3e2w1q!':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'token': 'admin_session_token',
                    'user': {
                        'email': email,
                        'role': 'admin'
                    }
                })
            }
        else:
            return {
                'statusCode': 401,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'message': '이메일 또는 비밀번호가 올바르지 않습니다.'
                })
            }
            
    except Exception as e:
        logger.error(f"Admin auth error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'message': '서버 오류가 발생했습니다.'
            })
        }