"""
챗봇 핸들러 - 간소화된 버전
"""

import json
from aws_lambda_powertools import Logger
try:
    from error_handler import handle_error
    from response_builder import build_response
    from logger_config import setup_logger
except ImportError:
    # 테스트 환경에서는 기본 처리
    def handle_error(e, msg):
        return {'statusCode': 500, 'body': '{"error": "' + msg + '"}'}
    def build_response(data, status=200):
        import json
        return {'statusCode': status, 'body': json.dumps(data)}
    def setup_logger(name):
        from aws_lambda_powertools import Logger
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
        message = body.get("message", "")
        return {
            "message": f"안녕하세요! '{message}'에 대해 도움을 드리겠습니다.",
            "type": "response"
        }
        
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