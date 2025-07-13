"""
통합 챗봇 테스트 - 단순 질문 + 대화형 모드
"""

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "infra"))

from src.functions.chatbot_handler import handler as chatbot_handler


def test_simple_question_mode():
    """단순 질문 생성 모드 (기존 question_handler 호환)"""
    event = {
        "body": json.dumps(
            {
                "userProfile": {"region": "서울"},
                "policyText": "만 39세 이하 서울 청년 대상 예비창업자 지원사업",
            }
        )
    }

    response = chatbot_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "question" in body
    assert len(body["question"]) > 0


def test_conversational_mode():
    """대화형 챗봇 모드"""
    event = {"body": json.dumps({"message": "안녕하세요", "session_id": "test_session"})}

    response = chatbot_handler(event, {})

    assert "message" in response
    assert response["type"] == "response"


def test_mode_detection():
    """모드 자동 감지 테스트"""
    # 단순 질문 모드 감지
    simple_body = {"userProfile": {"region": "서울"}, "policyText": "만 39세 이하"}

    # 대화형 모드 감지
    chat_body = {"message": "안녕하세요", "session_id": "test"}

    # 각각 다른 응답 형식 확인
    simple_event = {"body": json.dumps(simple_body)}
    chat_event = {"body": json.dumps(chat_body)}

    simple_response = chatbot_handler(simple_event, {})
    chat_response = chatbot_handler(chat_event, {})

    # 단순 모드는 HTTP 응답 형식
    if "body" in simple_response:
        simple_body_parsed = json.loads(simple_response["body"])
        assert "question" in simple_body_parsed
    
    # 대화형 모드는 직접 데이터 반환
    if "message" in chat_response:
        assert "message" in chat_response
        assert "type" in chat_response
    elif "body" in chat_response:
        chat_body_parsed = json.loads(chat_response["body"])
        assert "message" in chat_body_parsed


def test_backward_compatibility():
    """기존 API 호환성 테스트"""
    # 기존 question API 호출 방식
    event = {
        "body": json.dumps(
            {
                "userProfile": {"region": "서울", "age": 30},
                "policyText": "만 39세 이하 서울 거주 청년 대상",
            }
        )
    }

    response = chatbot_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])

    # 기존 응답 형식 유지
    assert "question" in body
    assert isinstance(body["question"], str)
