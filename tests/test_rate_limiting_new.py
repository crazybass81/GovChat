"""
Rate Limiting 및 API 인증 테스트
"""

import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "infra"))

from src.common.api_auth import check_authorization, validate_api_key
from src.common.rate_limiter import RateLimiter, get_rate_limiter


def test_rate_limiter():
    """Rate Limiter 기본 동작 테스트"""
    limiter = RateLimiter(rate_limit=5, burst_limit=10)

    # Burst 허용 확인
    allowed_count = 0
    for _ in range(15):
        if limiter.allow_request():
            allowed_count += 1

    assert allowed_count == 10  # Burst limit

    # Rate limit 확인
    time.sleep(0.2)  # 토큰 리필 대기
    assert limiter.allow_request()


def test_endpoint_rate_limiters():
    """엔드포인트별 Rate Limiter 테스트"""
    chat_limiter = get_rate_limiter("chat")
    search_limiter = get_rate_limiter("search")

    assert chat_limiter.rate_limit == 10
    assert search_limiter.rate_limit == 50


def test_api_key_validation():
    """API 키 검증 테스트"""
    # 환경변수 설정
    os.environ["VALID_API_KEYS"] = "test-key-123,another-key-456"

    assert validate_api_key("test-key-123")
    assert validate_api_key("another-key-456")
    assert not validate_api_key("invalid-key")
    assert not validate_api_key("short")


def test_authorization_check():
    """인증 체크 테스트"""
    os.environ["VALID_API_KEYS"] = "test-api-key-12345"

    # API Key 인증
    event_with_api_key = {"headers": {"X-API-Key": "test-api-key-12345"}}

    is_auth, auth_info = check_authorization(event_with_api_key)
    assert is_auth
    assert auth_info["auth_type"] == "api_key"

    # 인증 실패
    event_no_auth = {"headers": {}}
    is_auth, auth_info = check_authorization(event_no_auth)
    assert not is_auth
    assert auth_info is None
