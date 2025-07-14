"""
챗봇 핸들러 - 간소화된 버전
"""

import json
from aws_lambda_powertools import Logger
try:
    from functions.error_handler import handle_error
    from functions.response_builder import build_response
    from functions.logger_config import setup_logger
except ImportError:
    # 테스트 환경에서는 기본 처리
    def handle_error(e, msg):
        return {'statusCode': 500, 'body': json.dumps({'error': msg})}
    def build_response(data, status=200):
        return {'statusCode': status, 'body': json.dumps(data, ensure_ascii=False)}
    def setup_logger(name):
        return Logger()

logger = setup_logger(__name__)

def handler(event, context):
    """통합 챗봇 핸들러"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        logger.info("Chatbot request received", extra={"body_keys": list(body.keys())})
        
        # 단순 질문 생성 모드
        if "policyText" in body and "userProfile" in body:
            return handle_simple_question(body)
        
        # 대화형 모드
        message = body.get("message", "").strip()
        session_id = body.get("session_id", "default")
        
        # 인사말 처리 - 동의 요청
        if message in ["안녕하세요", "안녕", "hello", "hi"] or not message:
            return build_response({
                "message": "안녕하세요! 정부 지원사업 매칭 서비스입니다. 개인정보 처리에 동의하시겠습니까?",
                "type": "consent",
                "session_id": session_id
            })
        
        # 동의 처리 - 첫 질문
        if "동의" in message.lower():
            return build_response({
                "message": "감사합니다! 거주 중인 시·도를 알려주실 수 있나요?",
                "type": "question",
                "options": ["서울", "경기", "인천", "기타"],
                "session_id": session_id
            })
        
        # 기본 응답
        return build_response({
            "message": f"'{message}'에 대해 도움을 드리겠습니다.",
            "type": "response",
            "session_id": session_id
        })
        
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

# 테스트용 alias
lambda_handler = handler