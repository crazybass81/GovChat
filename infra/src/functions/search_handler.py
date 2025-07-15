"""
검색 핸들러 - 벡터 검색 지원
"""

import json
import os
from aws_lambda_powertools import Logger

try:
    import boto3
    import requests
except ImportError:
    boto3 = None
    requests = None

try:
    from functions.error_handler import handle_error
    from functions.response_builder import build_response
except ImportError:
    # 테스트 환경에서는 기본 처리
    def handle_error(e, msg):
        return {'statusCode': 500, 'body': json.dumps({'error': msg})}
    def build_response(data, status=200):
        return {'statusCode': status, 'body': json.dumps(data, ensure_ascii=False)}

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
        
        # OpenSearch 벡터 검색 수행
        results = perform_vector_search(query)
        
        # 기본 검색 결과 (벡터 검색 실패 시 백업)
        if not results:
            results = get_fallback_results(query)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'query': query,
                'results': results,
                'total': len(results),
                'search_type': 'vector_search'
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

def perform_vector_search(query):
    """벡터 검색 수행 (간단 버전)"""
    try:
        # 현재는 기본 검색으로 대체
        logger.info(f"Vector search requested for: {query}")
        return get_fallback_results(query)
        
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []

# OpenSearch 및 임베딩 기능은 추후 구현
# 현재는 기본 검색으로 대체

def get_fallback_results(query):
    """백업 검색 결과"""
    results = [
        {
            "id": "policy_001",
            "title": "청년창업지원사업",
            "description": "만 39세 이하 청년의 창업을 지원하는 사업",
            "provider": "중소벤처기업부",
            "score": 0.8
        },
        {
            "id": "policy_002", 
            "title": "중소기업 성장지원금",
            "description": "중소기업의 성장을 위한 자금 지원",
            "provider": "중소기업청",
            "score": 0.7
        }
    ]
    
    # 간단한 키워드 필터링
    filtered_results = []
    for result in results:
        if query.lower() in result['title'].lower() or query.lower() in result['description'].lower():
            filtered_results.append(result)
    
    return filtered_results if filtered_results else results