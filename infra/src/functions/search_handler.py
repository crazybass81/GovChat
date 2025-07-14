"""
검색 핸들러 - 간단한 버전
"""

import json
import os
from aws_lambda_powertools import Logger

logger = Logger()

def handler(event, context):
    """검색 Lambda 핸들러"""
    try:
        # GET 요청의 쿼리 파라미터 처리
        query_params = event.get('queryStringParameters') or {}
        query = query_params.get('q', '')
        
        # POST 요청의 body도 지원
        if not query and event.get('body'):
            body = json.loads(event.get('body', '{}'))
            query = body.get('q', '')
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': '검색어(q)가 필요합니다',
                    'example': '/search?q=창업지원'
                }, ensure_ascii=False)
            }
        
        logger.info("Search request", extra={"query": query, "method": event.get('httpMethod')})
        
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
        
        # 검색어에 따른 필터링 (간단한 예시)
        filtered_results = []
        for result in results:
            if query.lower() in result['title'].lower() or query.lower() in result['description'].lower():
                filtered_results.append(result)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'query': query,
                'results': filtered_results,
                'total': len(filtered_results)
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error("Search handler error", extra={"error": str(e)})
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': '검색 처리 중 오류가 발생했습니다'
            }, ensure_ascii=False)
        }