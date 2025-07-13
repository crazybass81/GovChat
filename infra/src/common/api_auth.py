"""
API 인증 구현
"""

import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional


def validate_api_key(api_key: str) -> bool:
    """API 키 검증"""
    if not api_key:
        return False

    # 환경변수에서 유효한 API 키들 로드
    valid_keys_str = os.environ.get("VALID_API_KEYS", "")
    if not valid_keys_str:
        return False

    valid_keys = [k.strip() for k in valid_keys_str.split(",") if k.strip()]
    return api_key in valid_keys


def validate_jwt_token(token: str) -> Optional[Dict]:
    """JWT 토큰 검증 (간단한 구현)"""
    try:
        # Bearer 토큰에서 실제 토큰 추출
        if token.startswith("Bearer "):
            token = token[7:]

        # 간단한 토큰 검증 (실제로는 JWT 라이브러리 사용)
        parts = token.split(".")
        if len(parts) != 3:
            return None

        # 페이로드 디코딩 (실제로는 서명 검증 필요)
        import base64

        payload = base64.b64decode(parts[1] + "==")
        user_data = json.loads(payload)

        # 만료 시간 확인
        if user_data.get("exp", 0) < time.time():
            return None

        return user_data
    except Exception:
        return None


def check_authorization(event: Dict) -> tuple[bool, Optional[Dict]]:
    """요청 인증 확인"""
    headers = event.get("headers", {})

    # API Key 확인
    api_key = headers.get("X-API-Key") or headers.get("x-api-key")
    if api_key and validate_api_key(api_key):
        return True, {"auth_type": "api_key", "api_key": api_key}

    # JWT 토큰 확인
    auth_header = headers.get("Authorization") or headers.get("authorization")
    if auth_header:
        user_data = validate_jwt_token(auth_header)
        if user_data:
            return True, {"auth_type": "jwt", "user": user_data}

    return False, None


def generate_api_key(user_id: str) -> str:
    """API 키 생성"""
    timestamp = str(int(time.time()))
    secret = os.environ.get("API_KEY_SECRET", "default-secret")

    raw_key = f"{user_id}:{timestamp}"
    signature = hmac.new(secret.encode(), raw_key.encode(), hashlib.sha256).hexdigest()

    return f"{raw_key}:{signature}"
