"""
검색 핸들러
"""

import json
from aws_lambda_powertools import Logger
from error_handler import handle_error
from response_builder import build_response
from logger_config import setup_logger

logger = setup_logger(__name__)

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
        
        return build_response({
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return handle_error(e, "검색 처리 중 오류가 발생했습니다")