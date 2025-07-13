"""
통합 테스트
"""

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "infra"))

from src.functions.extract_handler import handler as extract_handler
from src.functions.question_handler import handler as question_handler


def test_question_handler_integration():
    """질문 핸들러 통합 테스트"""
    event = {
        "body": json.dumps(
            {
                "userProfile": {"region": "서울"},
                "policyText": "만 39세 이하 서울 청년 대상 예비창업자 지원사업",
            }
        )
    }

    response = question_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "question" in body
    assert len(body["question"]) > 0


def test_extract_handler_integration():
    """추출 핸들러 통합 테스트"""
    event = {"body": json.dumps({"policyText": "만 39세 이하 서울 거주 청년 대상 창업 지원"})}

    response = extract_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "age" in body
    assert body["age"]["max"] == 39


def test_security_headers():
    """보안 헤더 테스트"""
    event = {"body": json.dumps({"userProfile": {"region": "서울"}, "policyText": "테스트"})}

    response = question_handler(event, {})
    headers = response["headers"]

    assert "X-Content-Type-Options" in headers
    assert "X-Frame-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
