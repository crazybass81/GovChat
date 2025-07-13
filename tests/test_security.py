"""
보안 테스트
"""

import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.common.circuit_breaker import CircuitBreaker
from src.common.xss_protection import sanitize_input, validate_json_input


def test_xss_sanitization():
    """XSS 공격 방지 테스트"""
    malicious_input = "<script>alert('xss')</script>Hello"
    result = sanitize_input(malicious_input)
    assert "<script>" not in result
    assert "Hello" in result


def test_circuit_breaker():
    """Circuit Breaker 테스트"""

    def failing_function():
        raise Exception("API Error")

    cb = CircuitBreaker(failure_threshold=2, timeout=1)

    # 첫 번째 실패
    with pytest.raises(Exception, match="API Error"):
        cb.call(failing_function)

    # 두 번째 실패 - Circuit 열림
    with pytest.raises(Exception, match="API Error"):
        cb.call(failing_function)

    # Circuit이 열린 상태에서 호출
    with pytest.raises(Exception, match="Circuit breaker is OPEN"):
        cb.call(failing_function)


def test_json_validation():
    """JSON 입력 검증 테스트"""
    malicious_data = {
        "message": "<script>alert('hack')</script>안녕하세요",
        "user": {"name": "onclick='alert(1)'테스트"},
    }

    cleaned = validate_json_input(malicious_data)
    assert "<script>" not in cleaned["message"]
    assert "onclick=" not in cleaned["user"]["name"]
    assert "안녕하세요" in cleaned["message"]
