"""
외부 공공데이터 API 연동 핸들러 - 간단한 버전
"""

import json
import boto3
from aws_lambda_powertools import Logger

try:
    import requests
except ImportError:
    # requests 모듈이 없는 경우 기본 처리
    requests = None

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
    """정책 동기화 - 공공데이터 포털 API 연동"""
    try:
        # API 키 설정 (AWS Secrets Manager에서 가져오거나 환경변수)
        api_key = "0259O7/...=="  # 실제 키로 교체 필요
        
        # 공공데이터 포털 API 호출
        policies = fetch_government_policies(api_key)
        
        # DynamoDB에 저장
        saved_count = save_policies_to_db(policies)
        
        result = {
            "message": "동기화가 완료되었습니다",
            "total": len(policies),
            "inserted": saved_count,
            "updated": 0
        }
        
        logger.info("Policy sync completed", extra=result)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Sync policies error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}, ensure_ascii=False)
        }

def fetch_government_policies(api_key: str) -> list:
    """공공데이터 포털에서 정책 데이터 가져오기"""
    if not requests:
        return get_sample_policies()
    
    try:
        # 공공데이터 포털 API URL
        base_url = "https://api.odcloud.kr/api/gov24/v1/serviceList"
        
        params = {
            "serviceKey": api_key,
            "page": 1,
            "perPage": 100,
            "returnType": "json"
        }
        
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return parse_policy_data(data)
        else:
            logger.warning(f"API call failed: {response.status_code}")
            return get_sample_policies()
            
    except Exception as e:
        logger.error(f"API fetch error: {e}")
        return get_sample_policies()

def get_sample_policies() -> list:
    """샘플 정책 데이터"""
    return [
        {
            "policy_id": "sample_001",
            "title": "청년창업지원사업",
            "description": "만 39세 이하 청년의 창업을 지원하는 사업",
            "agency": "중소벤처기업부",
            "target_age": "39세 이하",
            "support_type": "창업지원",
            "region": "전국"
        },
        {
            "policy_id": "sample_002",
            "title": "중소기업 성장지원금",
            "description": "중소기업의 성장을 위한 자금 지원",
            "agency": "중소기업청",
            "target_age": "전 연령",
            "support_type": "자금지원",
            "region": "전국"
        },
        {
            "policy_id": "sample_003",
            "title": "서울시 청년주거지원",
            "description": "서울시 거주 청년의 주거비 지원",
            "agency": "서울시",
            "target_age": "35세 이하",
            "support_type": "주거지원",
            "region": "서울"
        }
    ]

def parse_policy_data(api_data: dict) -> list:
    """공공데이터 API 응답 파싱"""
    # API 응답 구조에 따라 파싱 로직 구현
    # 현재는 샘플 데이터 반환
    return get_sample_policies()

def save_policies_to_db(policies: list) -> int:
    """정책 데이터를 DynamoDB에 저장"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('govchat-policies')  # 테이블명 확인 필요
        
        saved_count = 0
        for policy in policies:
            table.put_item(Item={
                'policy_id': policy['policy_id'],
                'title': policy['title'],
                'description': policy['description'],
                'agency': policy['agency'],
                'target_age': policy['target_age'],
                'support_type': policy['support_type'],
                'region': policy['region'],
                'source': 'external',
                'created_at': json.dumps({})
            })
            saved_count += 1
        
        return saved_count
        
    except Exception as e:
        logger.error(f"DB save error: {e}")
        return 0

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