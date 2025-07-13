"""
질문 핸들러 - 단순 질문 생성 모드
"""

import json
from aws_lambda_powertools import Logger

logger = Logger()


def handler(event, context):
    """질문 생성 Lambda 핸들러 (기존 API 호환)"""
    try:
        body = json.loads(event.get('body', '{}'))
        user_profile = body.get('userProfile', {})
        policy_text = body.get('policyText', '')
        
        logger.info("Question generation request", extra={
            "user_profile": user_profile,
            "policy_text_length": len(policy_text)
        })
        
        # 프로필 기반 질문 생성
        question = generate_question(user_profile, policy_text)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY'
            },
            'body': json.dumps({
                "question": question
            })
        }
        
    except Exception as e:
        logger.error("Question handler error", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }


def generate_question(user_profile: dict, policy_text: str) -> str:
    """사용자 프로필과 정책 텍스트 기반 질문 생성"""
    
    # 필수 정보 확인 순서
    if not user_profile.get('region'):
        return "거주 중인 시·도를 알려주실 수 있나요?"
    
    if not user_profile.get('age'):
        return "연령대를 알려주시면 맞춤 지원사업을 찾을 수 있어요."
    
    if not user_profile.get('business_status'):
        return "사업자등록이 되어 있으신가요?"
    
    if not user_profile.get('income_level'):
        return "소득 수준은 어느 정도인가요? (저소득/중간소득/고소득)"
    
    # 정책 텍스트 기반 추가 질문
    if "창업" in policy_text and not user_profile.get('startup_stage'):
        return "창업 준비 단계는 어느 정도인가요? (아이디어/준비중/운영중)"
    
    if "청년" in policy_text and not user_profile.get('age_verified'):
        return "정확한 나이를 알려주시면 청년 지원사업 해당 여부를 확인할 수 있어요."
    
    # 모든 정보가 충분한 경우
    return "필요한 정보를 모두 수집했습니다! 맞춤 지원사업을 찾아드릴게요."