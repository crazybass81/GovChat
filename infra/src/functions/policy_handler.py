"""
A2: 정책 CRUD 확장 Lambda 핸들러
"""

import json
import uuid
from datetime import datetime

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from common.xss_protection import sanitize_input, secure_headers

logger = Logger()
tracer = Tracer()
metrics = Metrics()

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
policies_table = dynamodb.Table("PoliciesTable")
versions_table = dynamodb.Table("PolicyVersionTable")


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def handler(event, context):
    """정책 CRUD 핸들러"""
    try:
        headers = secure_headers()

        if event["httpMethod"] == "OPTIONS":
            return {"statusCode": 200, "headers": headers, "body": ""}

        method = event["httpMethod"]
        path = event["resource"]

        if method == "GET" and path == "/policies":
            return _list_policies(headers)
        elif method == "POST" and path == "/policies":
            return _create_policy(event.get("body", "{}"), headers)
        elif method == "GET" and path == "/policies/{id}":
            policy_id = event["pathParameters"]["id"]
            return _get_policy(policy_id, headers)
        elif method == "PUT" and path == "/policies/{id}":
            policy_id = event["pathParameters"]["id"]
            return _update_policy(policy_id, event.get("body", "{}"), headers)
        elif method == "POST" and path == "/policies/{id}:publish":
            policy_id = event["pathParameters"]["id"]
            return _publish_policy(policy_id, headers)
        elif method == "POST" and path == "/admin/api-registry":
            return _handle_api_registry(event.get("body", "{}"), headers)
        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Not found"}),
            }

    except Exception as e:
        logger.error(f"Policy handler error: {e}")
        metrics.add_metric(name="PolicyError", unit=MetricUnit.Count, value=1)
        return {
            "statusCode": 500,
            "headers": secure_headers(),
            "body": json.dumps({"error": "Internal server error"}),
        }


@tracer.capture_method
def _list_policies(headers: dict):
    """정책 목록 조회"""
    try:
        response = policies_table.scan()
        policies = response.get("Items", [])

        metrics.add_metric(name="PolicyList", unit=MetricUnit.Count, value=1)

        return {"statusCode": 200, "headers": headers, "body": json.dumps(policies)}
    except Exception as e:
        logger.error(f"List policies error: {e}")
        raise


@tracer.capture_method
def _get_policy(policy_id: str, headers: dict):
    """정책 상세 조회"""
    try:
        # 최신 정책 정보 조회
        policy_response = policies_table.get_item(Key={"id": policy_id})

        if "Item" not in policy_response:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Policy not found"}),
            }

        policy = policy_response["Item"]

        # 버전 목록 조회
        versions_response = versions_table.query(
            KeyConditionExpression="policy_id = :pid",
            ExpressionAttributeValues={":pid": policy_id},
            ScanIndexForward=False,  # 최신순 정렬
        )

        policy["versions"] = versions_response.get("Items", [])

        metrics.add_metric(name="PolicyGet", unit=MetricUnit.Count, value=1)

        return {"statusCode": 200, "headers": headers, "body": json.dumps(policy)}
    except Exception as e:
        logger.error(f"Get policy error: {e}")
        raise


@tracer.capture_method
def _create_policy(body: str, headers: dict):
    """정책 생성"""
    try:
        data = json.loads(body)
        yaml_content = sanitize_input(data.get("yaml", ""))

        if not yaml_content:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "YAML content required"}),
            }

        policy_id = str(uuid.uuid4())
        version = datetime.utcnow().isoformat()

        # S3에 YAML 저장
        s3_key = f"policies/{policy_id}/{version}.yaml"
        s3.put_object(
            Bucket="gov-support-policies", Key=s3_key, Body=yaml_content, ContentType="text/yaml"
        )

        # 정책 메타데이터 저장
        policy = {
            "id": policy_id,
            "version": version,
            "status": "DRAFT",
            "yaml": yaml_content,
            "yaml_s3_key": s3_key,
            "created_at": datetime.utcnow().isoformat(),
        }

        policies_table.put_item(Item=policy)

        # 버전 히스토리 저장
        version_record = {
            "policy_id": policy_id,
            "version": version,
            "status": "DRAFT",
            "yaml_s3_key": s3_key,
            "created_by": "admin",  # TODO: JWT에서 사용자 정보 추출
            "created_at": datetime.utcnow().isoformat(),
        }

        versions_table.put_item(Item=version_record)

        metrics.add_metric(name="PolicyCreate", unit=MetricUnit.Count, value=1)
        logger.info(f"Policy created: {policy_id}")

        return {"statusCode": 201, "headers": headers, "body": json.dumps(policy)}

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid JSON"}),
        }
    except Exception as e:
        logger.error(f"Create policy error: {e}")
        raise


@tracer.capture_method
def _update_policy(policy_id: str, body: str, headers: dict):
    """정책 업데이트"""
    try:
        data = json.loads(body)
        yaml_content = sanitize_input(data.get("yaml", ""))

        if not yaml_content:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "YAML content required"}),
            }

        # 기존 정책 확인
        policy_response = policies_table.get_item(Key={"id": policy_id})

        if "Item" not in policy_response:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Policy not found"}),
            }

        # 새 버전 생성
        new_version = datetime.utcnow().isoformat()
        s3_key = f"policies/{policy_id}/{new_version}.yaml"

        # S3에 새 버전 저장
        s3.put_object(
            Bucket="gov-support-policies", Key=s3_key, Body=yaml_content, ContentType="text/yaml"
        )

        # 정책 업데이트
        updated_policy = {
            "id": policy_id,
            "version": new_version,
            "status": "DRAFT",
            "yaml": yaml_content,
            "yaml_s3_key": s3_key,
            "updated_at": datetime.utcnow().isoformat(),
        }

        policies_table.put_item(Item=updated_policy)

        # 버전 히스토리 추가
        version_record = {
            "policy_id": policy_id,
            "version": new_version,
            "status": "DRAFT",
            "yaml_s3_key": s3_key,
            "created_by": "admin",
            "created_at": datetime.utcnow().isoformat(),
        }

        versions_table.put_item(Item=version_record)

        metrics.add_metric(name="PolicyUpdate", unit=MetricUnit.Count, value=1)
        logger.info(f"Policy updated: {policy_id}, version: {new_version}")

        return {"statusCode": 200, "headers": headers, "body": json.dumps(updated_policy)}

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid JSON"}),
        }
    except Exception as e:
        logger.error(f"Update policy error: {e}")
        raise


@tracer.capture_method
def _publish_policy(policy_id: str, headers: dict):
    """정책 발행"""
    try:
        # 기존 정책 확인
        policy_response = policies_table.get_item(Key={"id": policy_id})

        if "Item" not in policy_response:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Policy not found"}),
            }

        policy = policy_response["Item"]

        if policy["status"] == "PUBLISHED":
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Policy already published"}),
            }

        # 상태를 PUBLISHED로 변경
        policy["status"] = "PUBLISHED"
        policy["published_at"] = datetime.utcnow().isoformat()

        policies_table.put_item(Item=policy)

        # 버전 히스토리 업데이트
        versions_table.update_item(
            Key={"policy_id": policy_id, "version": policy["version"]},
            UpdateExpression="SET #status = :status, published_at = :published_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "PUBLISHED",
                ":published_at": datetime.utcnow().isoformat(),
            },
        )

        metrics.add_metric(name="PolicyPublish", unit=MetricUnit.Count, value=1)
        logger.info(f"Policy published: {policy_id}")

        return {"statusCode": 200, "headers": headers, "body": json.dumps(policy)}

    except Exception as e:
        logger.error(f"Publish policy error: {e}")
        raise


@tracer.capture_method
def _handle_api_registry(body: str, headers: dict):
    """API 레지스트리 처리"""
    try:
        data = json.loads(body)
        action = data.get('action')
        
        if action == 'save_api_config':
            config = data.get('config', {})
            
            # DynamoDB에 API 설정 저장
            api_item = {
                "id": config.get('id'),
                "name": config.get('name'),
                "url": config.get('url'),
                "serviceKey": config.get('serviceKey'),
                "type": "government_api",
                "status": "active",
                "createdAt": config.get('createdAt')
            }
            
            policies_table.put_item(Item=api_item)
            logger.info(f"API config saved: {config.get('id')}")
            
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"success": True, "saved": 1})
            }
        
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid action"})
        }
        
    except Exception as e:
        logger.error(f"API registry error: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": "Internal server error"})
        }
