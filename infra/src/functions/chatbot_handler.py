"""
챗봇 핸들러 - 간소화된 버전
"""

import json
from aws_lambda_powertools import Logger

logger = Logger()

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
        logger.error("Chatbot error", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_simple_question(body: dict) -> dict:
    """단순 질문 생성"""
    user_profile = body["userProfile"]
    
    if not user_profile.get('region'):
        question = "거주 중인 시·도를 알려주실 수 있나요?"
    elif not user_profile.get('age'):
        question = "연령대를 알려주시면 맞춤 지원사업을 찾을 수 있어요."
    else:
        question = "필요한 정보를 모두 수집했습니다!"
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        },
        'body': json.dumps({"question": question})
    }