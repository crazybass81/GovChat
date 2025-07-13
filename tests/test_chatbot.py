"""
챗봇 기능 테스트
"""

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "infra"))

from src.chatbot.conversation_engine import ConversationEngine, QuestionMetadata
from src.functions.chatbot_handler import handler as chatbot_handler


def test_conversation_engine():
    """대화 엔진 테스트"""
    engine = ConversationEngine()

    # 정보 추출 테스트
    message = "저는 서울에 살고 30대입니다"
    extracted = engine.extract_user_info(message, {})

    assert extracted["region"] == "서울"
    assert extracted["age_group"] == "30대"


def test_next_question_selection():
    """다음 질문 선택 테스트"""
    engine = ConversationEngine()

    user_profile = {"region": "서울"}
    questions_asked = ["region"]

    next_q = engine.get_next_question(user_profile, questions_asked)

    assert next_q is not None
    assert next_q.field != "region"
    assert isinstance(next_q, QuestionMetadata)


def test_chatbot_handler_greeting():
    """챗봇 핸들러 인사 테스트"""
    event = {"body": json.dumps({"message": "안녕하세요", "session_id": "test_session"})}

    response = chatbot_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "동의" in body["message"]
    assert body["type"] == "consent"


def test_chatbot_handler_consent():
    """챗봇 핸들러 동의 테스트"""
    event = {"body": json.dumps({"message": "동의", "session_id": "test_session"})}

    response = chatbot_handler(event, {})

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["type"] == "question"
    assert "options" in body


def test_information_extraction():
    """정보 추출 정확도 테스트"""
    engine = ConversationEngine()

    test_cases = [
        ("서울에 살고 있어요", {"region": "서울"}),
        ("20대 청년입니다", {"age_group": "20대"}),
        ("사업자등록 되어있어요", {"business_status": "예"}),
        ("사업자등록 안되어있어요", {"business_status": "아니오"}),
    ]

    for message, expected in test_cases:
        extracted = engine.extract_user_info(message, {})
        for key, value in expected.items():
            assert extracted.get(key) == value


def test_sensitivity_handling():
    """민감도 처리 테스트"""
    engine = ConversationEngine()

    # 민감도 높은 질문 확인
    tax_question = None
    for q in engine.question_bank:
        if q.field == "tax_status":
            tax_question = q
            break

    assert tax_question is not None
    assert tax_question.sensitivity == 0.9
    assert tax_question.requires_consent
