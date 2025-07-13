"""
검색 핸들러
"""

import json
from aws_lambda_powertools import Logger

logger = Logger()

def handler(event, context):
    """검색 Lambda 핸들러"""
    try:
        body = json.loads(event.get('body', '{}'))
        query = body.get('q', '')
        
        logger.info("Search request", extra={"query": query})
        
        # 간단한 검색 결과 반환
        results = [
            {
                "id": "policy_001",
                "title": "청년창업지원사업",
                "description": "만 39세 이하 청년의 창업을 지원하는 사업",
                "provider": "중소벤처기업부"
            },
            {
                "id": "policy_002", 
                "title": "중소기업 성장지원금",
                "description": "중소기업의 성장을 위한 자금 지원",
                "provider": "중소기업청"
            }
        ]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY'
            },
            'body': json.dumps({
                'results': results,
                'total': len(results)
            })
        }
        
    except Exception as e:
        logger.error("Search error", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }