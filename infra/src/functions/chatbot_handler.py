"""
챗봇 핸들러 - AI 기반 지능형 대화
"""

import json
from aws_lambda_powertools import Logger
try:
    from functions.error_handler import handle_error
    from functions.response_builder import build_response
    from functions.logger_config import setup_logger
    from chatbot.conversation_engine import ConversationEngine
except ImportError:
    # 테스트 환경에서는 기본 처리
    def handle_error(e, msg):
        return {'statusCode': 500, 'body': json.dumps({'error': msg})}
    def build_response(data, status=200):
        return {'statusCode': status, 'body': json.dumps(data, ensure_ascii=False)}
    def setup_logger(name):
        return Logger()
    
    # 기본 대화 엔진
    class ConversationEngine:
        def extract_user_info(self, message, profile):
            return profile
        def get_next_question(self, profile, asked):
            return None
        def should_end_conversation(self, profile, asked):
            return len(asked) > 3

logger = setup_logger(__name__)
conversation_engine = ConversationEngine()

def handler(event, context):
    """통합 챗봇 핸들러"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        logger.info("Chatbot request received", extra={"body_keys": list(body.keys())})
        
        # 단순 질문 생성 모드
        if "policyText" in body and "userProfile" in body:
            return handle_simple_question(body)
        
        # 대화형 모드 - AI 기반 지능형 대화
        message = body.get("message", "").strip()
        session_id = body.get("session_id", "default")
        user_profile = body.get("user_profile", {})
        questions_asked = body.get("questions_asked", [])
        
        # 인사말 처리 - 동의 요청
        if message in ["안녕하세요", "안녕", "hello", "hi"] or not message:
            return build_response({
                "message": "안녕하세요! 정부 지원사업 매칭 서비스입니다. 개인정보 처리에 동의하시겠습니까?",
                "type": "consent",
                "session_id": session_id,
                "user_profile": {},
                "questions_asked": []
            })
        
        # 동의 처리 - AI 기반 첫 질문
        if "동의" in message.lower():
            return handle_intelligent_conversation("동의합니다", session_id, {}, [])
        
        # AI 기반 대화 처리
        return handle_intelligent_conversation(message, session_id, user_profile, questions_asked)
        
    except Exception as e:
        return handle_error(e, "챗봇 처리 중 오류가 발생했습니다")

def handle_simple_question(body: dict) -> dict:
    """단순 질문 생성"""
    user_profile = body["userProfile"]
    
    if not user_profile.get('region'):
        question = "거주 중인 시·도를 알려주실 수 있나요?"
    elif not user_profile.get('age'):
        question = "연령대를 알려주시면 맞춤 지원사업을 찾을 수 있어요."
    else:
        question = "필요한 정보를 모두 수집했습니다!"
    
    return build_response({"question": question})

def handle_intelligent_conversation(message: str, session_id: str, user_profile: dict, questions_asked: list) -> dict:
    """지능형 대화 처리"""
    try:
        # 1. 사용자 메시지에서 조건 추출
        if message != "동의합니다":
            updated_profile = conversation_engine.extract_user_info(message, user_profile)
        else:
            updated_profile = user_profile.copy()
        
        logger.info("Profile updated", extra={
            "session_id": session_id,
            "before": user_profile,
            "after": updated_profile
        })
        
        # 2. 대화 종료 조건 확인
        if conversation_engine.should_end_conversation(updated_profile, questions_asked):
            return build_response({
                "message": f"감사합니다! 수집된 정보로 맞춤 지원사업을 찾아드리겠습니다. 현재 정보: {updated_profile}",
                "type": "result",
                "session_id": session_id,
                "user_profile": updated_profile,
                "questions_asked": questions_asked,
                "recommendations": generate_recommendations(updated_profile)
            })
        
        # 3. 다음 질문 선택
        next_question = conversation_engine.get_next_question(updated_profile, questions_asked)
        
        if next_question:
            questions_asked.append(next_question.field)
            return build_response({
                "message": next_question.question,
                "type": "question",
                "options": next_question.options or [],
                "session_id": session_id,
                "user_profile": updated_profile,
                "questions_asked": questions_asked
            })
        
        # 4. 더 이상 질문이 없으면 결과 제시
        return build_response({
            "message": "수집된 정보로 맞춤 지원사업을 찾아드리겠습니다!",
            "type": "result",
            "session_id": session_id,
            "user_profile": updated_profile,
            "questions_asked": questions_asked,
            "recommendations": generate_recommendations(updated_profile)
        })
        
    except Exception as e:
        logger.error("Intelligent conversation error", extra={"error": str(e)})
        return build_response({
            "message": "죄송합니다. 다시 시도해 주세요.",
            "type": "error",
            "session_id": session_id
        })

def generate_recommendations(user_profile: dict) -> list:
    """사용자 프로필 기반 추천 사업 생성"""
    # 기본 추천 로직 (추후 DB 연동)
    recommendations = [
        {
            "id": "policy_001",
            "title": "청년창업지원사업",
            "description": "만 39세 이하 청년의 창업을 지원하는 사업",
            "provider": "중소벤처기업부",
            "match_score": 0.85
        }
    ]
    
    # 프로필 기반 필터링 (간단한 예시)
    if user_profile.get("support_type") == "창업지원":
        recommendations[0]["match_score"] = 0.95
    
    return recommendations

# 테스트용 alias
lambda_handler = handler