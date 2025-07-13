"""
API 인증 및 권한 검증 공통 모듈
"""

import jwt
import boto3
from datetime import datetime
from aws_lambda_powertools import Logger

logger = Logger()
ssm = boto3.client('ssm')
dynamodb = boto3.resource("dynamodb")


def verify_token(headers):
    """JWT 토큰 검증"""
    try:
        # Authorization 헤더에서 토큰 추출
        auth_header = headers.get('Authorization') or headers.get('authorization')
        if not auth_header:
            return {"valid": False, "error": "토큰이 없습니다."}
        
        if not auth_header.startswith('Bearer '):
            return {"valid": False, "error": "잘못된 토큰 형식입니다."}
        
        token = auth_header.split(' ')[1]
        
        # JWT 시크릿 키 가져오기
        try:
            secret_key = ssm.get_parameter(
                Name='/govchat/jwt/secret',
                WithDecryption=True
            )['Parameter']['Value']
        except Exception:
            secret_key = "temp-secret-key"  # fallback
        
        # 토큰 검증
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # 토큰 블랙리스트 확인
        if _is_token_blacklisted(token):
            return {"valid": False, "error": "무효한 토큰입니다."}
        
        return {
            "valid": True,
            "user": {
                "email": payload.get("email"),
                "role": payload.get("role"),
                "exp": payload.get("exp")
            }
        }
        
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "토큰이 만료되었습니다."}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "유효하지 않은 토큰입니다."}
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return {"valid": False, "error": "토큰 검증 중 오류가 발생했습니다."}


def verify_admin_token(headers):
    """관리자 토큰 검증"""
    auth_result = verify_token(headers)
    
    if not auth_result["valid"]:
        return auth_result
    
    user = auth_result["user"]
    if user.get("role") != "admin":
        return {"valid": False, "error": "관리자 권한이 필요합니다."}
    
    return auth_result


def verify_user_token(headers):
    """일반 사용자 토큰 검증"""
    auth_result = verify_token(headers)
    
    if not auth_result["valid"]:
        return auth_result
    
    user = auth_result["user"]
    if user.get("role") not in ["user", "admin"]:
        return {"valid": False, "error": "사용자 권한이 필요합니다."}
    
    return auth_result


def require_verified_user(headers):
    """실명 인증된 사용자 검증"""
    auth_result = verify_user_token(headers)
    
    if not auth_result["valid"]:
        return auth_result
    
    user = auth_result["user"]
    
    # 사용자 정보에서 실명 인증 여부 확인
    try:
        user_table = dynamodb.Table("UserTable")
        user_data = user_table.get_item(Key={"email": user["email"]})
        
        if "Item" not in user_data:
            return {"valid": False, "error": "사용자를 찾을 수 없습니다."}
        
        if not user_data["Item"].get("verified", False):
            return {"valid": False, "error": "실명 인증이 필요합니다."}
        
        return auth_result
        
    except Exception as e:
        logger.error(f"User verification check error: {e}")
        return {"valid": False, "error": "사용자 검증 중 오류가 발생했습니다."}


def _is_token_blacklisted(token):
    """토큰 블랙리스트 확인"""
    try:
        # 토큰 해시 생성
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # 블랙리스트 테이블에서 확인
        blacklist_table = dynamodb.Table("TokenBlacklistTable")
        result = blacklist_table.get_item(Key={"token_hash": token_hash})
        
        if "Item" in result:
            # 만료 시간 확인
            expires_at = datetime.fromisoformat(result["Item"]["expires_at"])
            if datetime.utcnow() < expires_at:
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Blacklist check error: {e}")
        return False  # 에러 시 허용 (보안보다 가용성 우선)


def add_token_to_blacklist(token, expires_at):
    """토큰을 블랙리스트에 추가"""
    try:
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        blacklist_table = dynamodb.Table("TokenBlacklistTable")
        blacklist_table.put_item(
            Item={
                "token_hash": token_hash,
                "expires_at": expires_at.isoformat(),
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Add to blacklist error: {e}")
        return False


def rate_limit_check(client_id, max_requests=100, window_minutes=15):
    """Rate limiting 체크"""
    try:
        rate_limit_table = dynamodb.Table("RateLimitTable")
        now = datetime.utcnow()
        window_start = now.timestamp() - (window_minutes * 60)
        
        # 현재 윈도우의 요청 수 확인
        response = rate_limit_table.query(
            KeyConditionExpression="client_id = :client_id AND #timestamp > :window_start",
            ExpressionAttributeNames={"#timestamp": "timestamp"},
            ExpressionAttributeValues={
                ":client_id": client_id,
                ":window_start": window_start
            }
        )
        
        request_count = len(response.get("Items", []))
        
        if request_count >= max_requests:
            return {"allowed": False, "remaining": 0}
        
        # 현재 요청 기록
        rate_limit_table.put_item(
            Item={
                "client_id": client_id,
                "timestamp": now.timestamp(),
                "created_at": now.isoformat()
            }
        )
        
        return {"allowed": True, "remaining": max_requests - request_count - 1}
        
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        return {"allowed": True, "remaining": max_requests}  # 에러 시 허용