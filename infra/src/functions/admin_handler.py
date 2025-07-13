"""
관리자 기능 Lambda 핸들러
"""

import json
from datetime import datetime
import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from common.xss_protection import sanitize_input, secure_headers
from common.api_auth import verify_admin_token
from error_handler import handle_error
from response_builder import build_response
from logger_config import setup_logger

logger = setup_logger(__name__)
tracer = Tracer()
metrics = Metrics()

dynamodb = boto3.resource("dynamodb")
projects_table = dynamodb.Table("ProjectsTable")
admin_logs_table = dynamodb.Table("AdminLogsTable")


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def handler(event, context):
    """관리자 기능 핸들러"""
    try:
        headers = secure_headers()
        
        # 관리자 권한 확인
        auth_result = verify_admin_token(event.get("headers", {}))
        if not auth_result["valid"]:
            return {
                "statusCode": 403,
                "headers": headers,
                "body": json.dumps({"error": "관리자 권한이 필요합니다."})
            }
        
        admin_user = auth_result["user"]
        method = event["httpMethod"]
        path = event["resource"]
        
        if method == "POST" and path == "/admin/projects":
            return _create_project(event.get("body", "{}"), admin_user, headers)
        elif method == "PUT" and path == "/admin/projects/{id}":
            project_id = event["pathParameters"]["id"]
            return _update_project(project_id, event.get("body", "{}"), admin_user, headers)
        elif method == "DELETE" and path == "/admin/projects/{id}":
            project_id = event["pathParameters"]["id"]
            return _delete_project(project_id, admin_user, headers)
        elif method == "GET" and path == "/admin/logs":
            return _get_admin_logs(event.get("queryStringParameters", {}), headers)
        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Not found"})
            }
            
    except Exception as e:
        metrics.add_metric(name="AdminError", unit=MetricUnit.Count, value=1)
        return handle_error(e, "관리자 기능 처리 중 오류가 발생했습니다")


@tracer.capture_method
def _create_project(body, admin_user, headers):
    """프로젝트 생성"""
    try:
        data = json.loads(body)
        
        # 필수 필드 검증
        required_fields = ["title", "description", "agency"]
        for field in required_fields:
            if not data.get(field):
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({"error": f"{field}는 필수 입력 사항입니다."})
                }
        
        # 데이터 정제
        project_data = {
            "project_id": f"manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "title": sanitize_input(data["title"]),
            "description": sanitize_input(data["description"]),
            "agency": sanitize_input(data["agency"]),
            "target_audience": sanitize_input(data.get("target_audience", "")),
            "support_content": sanitize_input(data.get("support_content", "")),
            "application_period": sanitize_input(data.get("application_period", "")),
            "application_method": sanitize_input(data.get("application_method", "")),
            "required_documents": sanitize_input(data.get("required_documents", "")),
            "contact_info": sanitize_input(data.get("contact_info", "")),
            "reference_url": sanitize_input(data.get("reference_url", "")),
            "source": "manual",
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # 프로젝트 저장
        projects_table.put_item(Item=project_data)
        
        # 관리자 로그 기록
        _log_admin_action(
            admin_user["email"],
            "CREATE_PROJECT",
            "project",
            project_data["project_id"],
            {"title": project_data["title"], "agency": project_data["agency"]}
        )
        
        logger.info(f"Project created by admin: {project_data['project_id']}")
        metrics.add_metric(name="AdminProjectCreate", unit=MetricUnit.Count, value=1)
        
        return build_response({
            "message": "프로젝트가 성공적으로 생성되었습니다.",
            "project": project_data
        }, 201)
        
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid JSON"})
        }
    except Exception as e:
        logger.error(f"Create project error: {e}")
        raise


@tracer.capture_method
def _update_project(project_id, body, admin_user, headers):
    """프로젝트 수정"""
    try:
        data = json.loads(body)
        
        # 기존 프로젝트 확인
        existing = projects_table.get_item(Key={"project_id": project_id})
        if "Item" not in existing:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "프로젝트를 찾을 수 없습니다."})
            }
        
        # 업데이트 표현식 구성
        update_expression = "SET last_updated = :updated"
        expression_values = {":updated": datetime.utcnow().isoformat()}
        
        updatable_fields = [
            "title", "description", "agency", "target_audience",
            "support_content", "application_period", "application_method",
            "required_documents", "contact_info", "reference_url"
        ]
        
        updated_fields = []
        for field in updatable_fields:
            if field in data:
                update_expression += f", {field} = :{field}"
                expression_values[f":{field}"] = sanitize_input(str(data[field]))
                updated_fields.append(field)
        
        if not updated_fields:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "업데이트할 필드가 없습니다."})
            }
        
        # 프로젝트 업데이트
        projects_table.update_item(
            Key={"project_id": project_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        # 관리자 로그 기록
        _log_admin_action(
            admin_user["email"],
            "UPDATE_PROJECT",
            "project",
            project_id,
            {"updated_fields": updated_fields}
        )
        
        logger.info(f"Project updated by admin: {project_id}")
        metrics.add_metric(name="AdminProjectUpdate", unit=MetricUnit.Count, value=1)
        
        return build_response({"message": "프로젝트가 성공적으로 수정되었습니다."})
        
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid JSON"})
        }
    except Exception as e:
        logger.error(f"Update project error: {e}")
        raise


@tracer.capture_method
def _delete_project(project_id, admin_user, headers):
    """프로젝트 삭제 (소프트 삭제)"""
    try:
        # 기존 프로젝트 확인
        existing = projects_table.get_item(Key={"project_id": project_id})
        if "Item" not in existing:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "프로젝트를 찾을 수 없습니다."})
            }
        
        project = existing["Item"]
        
        # 소프트 삭제 (active = False)
        projects_table.update_item(
            Key={"project_id": project_id},
            UpdateExpression="SET active = :active, last_updated = :updated",
            ExpressionAttributeValues={
                ":active": False,
                ":updated": datetime.utcnow().isoformat()
            }
        )
        
        # 관리자 로그 기록
        _log_admin_action(
            admin_user["email"],
            "DELETE_PROJECT",
            "project",
            project_id,
            {"title": project.get("title")}
        )
        
        logger.info(f"Project deleted by admin: {project_id}")
        metrics.add_metric(name="AdminProjectDelete", unit=MetricUnit.Count, value=1)
        
        return build_response({"message": "프로젝트가 성공적으로 삭제되었습니다."})
        
    except Exception as e:
        logger.error(f"Delete project error: {e}")
        raise


@tracer.capture_method
def _get_admin_logs(query_params, headers):
    """관리자 활동 로그 조회"""
    try:
        limit = int(query_params.get("limit", 50))
        
        response = admin_logs_table.scan(
            Limit=limit,
            ScanIndexForward=False  # 최신순
        )
        
        logs = response.get("Items", [])
        
        return build_response({"logs": logs})
        
    except Exception as e:
        logger.error(f"Get admin logs error: {e}")
        raise


def _log_admin_action(admin_email, action, target_type, target_id, details):
    """관리자 활동 로그 기록"""
    try:
        log_item = {
            "log_id": f"{admin_email}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "admin_email": admin_email,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "details": details,
            "created_at": datetime.utcnow().isoformat()
        }
        
        admin_logs_table.put_item(Item=log_item)
        
    except Exception as e:
        logger.error(f"Admin log error: {e}")
        # 로그 실패는 메인 기능에 영향을 주지 않도록 함