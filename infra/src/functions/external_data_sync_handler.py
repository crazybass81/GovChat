"""
외부 공공데이터 API 연동 및 동기화 Lambda 핸들러
"""

import json
import requests
from datetime import datetime
import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from common.xss_protection import secure_headers

logger = Logger()
tracer = Tracer()
metrics = Metrics()

dynamodb = boto3.resource("dynamodb")
projects_table = dynamodb.Table("ProjectsTable")
ssm = boto3.client('ssm')


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def handler(event, context):
    """외부 데이터 동기화 핸들러"""
    try:
        headers = secure_headers()
        
        if event.get("source") == "aws.events":  # CloudWatch Events 스케줄러
            return _scheduled_sync()
        
        method = event.get("httpMethod")
        path = event.get("resource")
        
        if method == "POST" and path == "/admin/sync-policies":
            return _manual_sync(headers)
        elif method == "GET" and path == "/admin/search-external":
            keyword = event.get("queryStringParameters", {}).get("keyword", "")
            return _search_external(keyword, headers)
        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Not found"})
            }
            
    except Exception as e:
        logger.error(f"External data sync error: {e}")
        metrics.add_metric(name="SyncError", unit=MetricUnit.Count, value=1)
        return {
            "statusCode": 500,
            "headers": secure_headers(),
            "body": json.dumps({"error": "Internal server error"})
        }


@tracer.capture_method
def _scheduled_sync():
    """정기 스케줄 동기화"""
    try:
        keywords = ['청년', '창업', '중소기업', '지원사업']
        sync_results = {
            "total": 0,
            "inserted": 0,
            "updated": 0,
            "errors": []
        }
        
        for keyword in keywords:
            try:
                result = _sync_policies_by_keyword(keyword)
                sync_results["total"] += result["total"]
                sync_results["inserted"] += result["inserted"]
                sync_results["updated"] += result["updated"]
                sync_results["errors"].extend(result["errors"])
            except Exception as e:
                sync_results["errors"].append({
                    "keyword": keyword,
                    "error": str(e)
                })
        
        logger.info("Scheduled sync completed", extra=sync_results)
        metrics.add_metric(name="ScheduledSync", unit=MetricUnit.Count, value=1)
        
        return {"statusCode": 200, "body": json.dumps(sync_results)}
        
    except Exception as e:
        logger.error(f"Scheduled sync error: {e}")
        raise


@tracer.capture_method
def _manual_sync(headers):
    """수동 동기화"""
    try:
        keywords = ['청년', '창업', '중소기업', '지원사업']
        sync_results = {
            "total": 0,
            "inserted": 0,
            "updated": 0,
            "errors": []
        }
        
        for keyword in keywords:
            try:
                result = _sync_policies_by_keyword(keyword)
                sync_results["total"] += result["total"]
                sync_results["inserted"] += result["inserted"]
                sync_results["updated"] += result["updated"]
                sync_results["errors"].extend(result["errors"])
            except Exception as e:
                sync_results["errors"].append({
                    "keyword": keyword,
                    "error": str(e)
                })
        
        logger.info("Manual sync completed", extra=sync_results)
        metrics.add_metric(name="ManualSync", unit=MetricUnit.Count, value=1)
        
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "동기화가 완료되었습니다.",
                "results": sync_results
            })
        }
        
    except Exception as e:
        logger.error(f"Manual sync error: {e}")
        raise


@tracer.capture_method
def _search_external(keyword, headers):
    """외부 API 실시간 검색"""
    try:
        if not keyword:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "키워드가 필요합니다."})
            }
        
        policies = _fetch_external_policies(keyword)
        
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"policies": policies})
        }
        
    except Exception as e:
        logger.error(f"External search error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "외부 검색 중 오류가 발생했습니다."})
        }


@tracer.capture_method
def _sync_policies_by_keyword(keyword):
    """키워드별 정책 동기화"""
    result = {
        "total": 0,
        "inserted": 0,
        "updated": 0,
        "errors": []
    }
    
    try:
        policies = _fetch_external_policies(keyword)
        
        for policy in policies:
            try:
                action = _upsert_policy(policy)
                result["total"] += 1
                if action == "insert":
                    result["inserted"] += 1
                else:
                    result["updated"] += 1
            except Exception as e:
                result["errors"].append({
                    "policy_id": policy.get("policyId"),
                    "error": str(e)
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Sync by keyword error: {e}")
        raise


@tracer.capture_method
def _fetch_external_policies(keyword, page=1, num_of_rows=100):
    """외부 API에서 정책 데이터 가져오기"""
    try:
        # API 키 가져오기
        api_key = ssm.get_parameter(
            Name='/govchat/external/data-go-kr-api-key',
            WithDecryption=True
        )['Parameter']['Value']
        
        url = "https://api.data.go.kr/1360000/SupportPolicyService/getSupportPolicyList"
        params = {
            "serviceKey": api_key,
            "keyword": keyword,
            "pageNo": page,
            "numOfRows": num_of_rows,
            "type": "json"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("response", {}).get("header", {}).get("resultCode") == "00":
            return data.get("response", {}).get("body", {}).get("items", [])
        else:
            error_msg = data.get("response", {}).get("header", {}).get("resultMsg", "Unknown error")
            raise Exception(f"API Error: {error_msg}")
            
    except Exception as e:
        logger.error(f"Fetch external policies error: {e}")
        raise


@tracer.capture_method
def _upsert_policy(policy_data):
    """정책 데이터 삽입/업데이트"""
    try:
        mapped_data = _map_external_data(policy_data)
        
        # 기존 데이터 확인
        try:
            existing = projects_table.get_item(
                Key={"policy_external_id": mapped_data["policy_external_id"]}
            )
            
            if "Item" in existing:
                # 업데이트
                projects_table.update_item(
                    Key={"policy_external_id": mapped_data["policy_external_id"]},
                    UpdateExpression="""
                        SET title = :title, description = :desc, agency = :agency,
                        target_audience = :target, support_content = :support,
                        application_period = :period, last_updated = :updated
                    """,
                    ExpressionAttributeValues={
                        ":title": mapped_data["title"],
                        ":desc": mapped_data["description"],
                        ":agency": mapped_data["agency"],
                        ":target": mapped_data["target_audience"],
                        ":support": mapped_data["support_content"],
                        ":period": mapped_data["application_period"],
                        ":updated": datetime.utcnow().isoformat()
                    },
                    ConditionExpression="attribute_exists(policy_external_id) AND #source = :source",
                    ExpressionAttributeNames={"#source": "source"},
                    ExpressionAttributeValues={":source": "external"}
                )
                return "update"
            else:
                # 삽입
                mapped_data["source"] = "external"
                mapped_data["active"] = True
                mapped_data["created_at"] = datetime.utcnow().isoformat()
                mapped_data["last_updated"] = datetime.utcnow().isoformat()
                
                projects_table.put_item(Item=mapped_data)
                return "insert"
                
        except Exception as e:
            logger.error(f"Upsert policy error: {e}")
            raise
            
    except Exception as e:
        logger.error(f"Policy upsert error: {e}")
        raise


def _map_external_data(policy_data):
    """외부 데이터를 내부 스키마로 매핑"""
    return {
        "policy_external_id": policy_data.get("policyId", ""),
        "title": policy_data.get("policyName", ""),
        "description": policy_data.get("policyContent", ""),
        "agency": policy_data.get("organName", ""),
        "target_audience": policy_data.get("target", ""),
        "support_content": policy_data.get("supportContent", ""),
        "application_period": policy_data.get("applyPeriod", ""),
        "application_method": policy_data.get("applyMethod", ""),
        "contact_info": policy_data.get("contactInfo", ""),
        "reference_url": policy_data.get("referenceUrl", "")
    }