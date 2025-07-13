"""
매칭 핸들러
"""

import json
from aws_lambda_powertools import Logger

logger = Logger()

def handler(event, context):
    """매칭 Lambda 핸들러"""
    try:
        body = json.loads(event.get('body', '{}'))
        user_profile = body.get('userProfile', {})
        policy_text = body.get('policyText', '')
        
        logger.info("Match request", extra={
            "user_profile": user_profile,
            "policy_text_length": len(policy_text)
        })
        
        # 간단한 매칭 점수 계산
        score = 0.0
        
        # 나이 매칭
        if user_profile.get('age'):
            if user_profile['age'] <= 39:
                score += 0.4
        
        # 지역 매칭
        if user_profile.get('region') == '서울':
            score += 0.3
            
        # 기본 점수
        score += 0.3
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY'
            },
            'body': json.dumps({
                'match_score': round(score, 2),
                'eligible': score >= 0.7,
                'reasons': ['연령 조건 충족', '지역 조건 충족'] if score >= 0.7 else ['조건 미충족']
            })
        }
        
    except Exception as e:
        logger.error("Match error", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }