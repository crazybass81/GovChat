"""
외부 공공데이터 API 연동 핸들러 - 간단한 버전
"""

import json
import requests
import boto3
from aws_lambda_powertools import Logger

logger = Logger()

def handler(event, context):
    """외부 데이터 동기화 핸들러"""
    try:
        method = event.get("httpMethod")
        path = event.get("resource")
        
        if method == "POST" and "sync-policies" in path:
            return sync_policies()
        elif method == "GET" and "search-external" in path:
            keyword = event.get("queryStringParameters", {}).get("keyword", "")
            return search_external(keyword)
        else:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Not found"})
            }
            
    except Exception as e:
        logger.error(f"External sync error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }

def sync_policies():
    """정책 동기화"""
    try:
        # 간단한 테스트 응답
        result = {
            "message": "동기화가 완료되었습니다",
            "total": 0,
            "inserted": 0,
            "updated": 0,
            "note": "공공데이터 API 연동 구현 중"
        }
        
        logger.info("Manual sync completed", extra=result)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Sync policies error: {e}")
        raise

def search_external(keyword):
    """외부 API 검색"""
    try:
        if not keyword:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "키워드가 필요합니다"})
            }
        
        # 간단한 테스트 응답
        policies = [
            {
                "id": "ext_001",
                "title": f"{keyword} 관련 지원사업 1",
                "description": f"{keyword}을 위한 정부 지원사업",
                "agency": "중소벤처기업부"
            },
            {
                "id": "ext_002", 
                "title": f"{keyword} 관련 지원사업 2",
                "description": f"{keyword} 분야 성장 지원",
                "agency": "산업통상자원부"
            }
        ]
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "keyword": keyword,
                "policies": policies,
                "note": "공공데이터 API 연동 구현 중"
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Search external error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "외부 검색 중 오류가 발생했습니다"})
        }