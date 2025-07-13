"""
A3: 사용자 프로필 API Lambda 핸들러
"""

import json
from datetime import datetime

import boto3
import jsonschema
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from common.xss_protection import sanitize_input, secure_headers

logger = Logger()
tracer = Tracer()
metrics = Metrics()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("UserProfileTable")

# 사용자 프로필 스키마
USER_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
        "region": {"type": "string", "maxLength": 50},
        "employment": {"type": "string", "maxLength": 100},
        "income": {"type": "integer", "minimum": 0},
        "maritalStatus": {"type": "string", "maxLength": 20},
        "education": {"type": "string", "maxLength": 50},
        "businessType": {"type": "string", "maxLength": 100},
    },
    "additionalProperties": False,
}


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def handler(event, context):
    """사용자 프로필 핸들러"""
    try:
        headers = secure_headers()

        if event["httpMethod"] == "OPTIONS":
            return {"statusCode": 200, "headers": headers, "body": ""}

        user_id = event["pathParameters"]["uid"]
        method = event["httpMethod"]

        if method == "GET":
            return _get_profile(user_id, headers)
        elif method == "PUT":
            return _update_profile(user_id, event.get("body", "{}"), headers)
        else:
            return {
                "statusCode": 405,
                "headers": headers,
                "body": json.dumps({"error": "Method not allowed"}),
            }

    except Exception as e:
        logger.error(f"User profile error: {e}")
        metrics.add_metric(name="ProfileError", unit=MetricUnit.Count, value=1)
        return {
            "statusCode": 500,
            "headers": secure_headers(),
            "body": json.dumps({"error": "Internal server error"}),
        }


@tracer.capture_method
def _get_profile(user_id: str, headers: dict):
    """프로필 조회"""
    try:
        response = table.get_item(Key={"user_id": user_id})

        if "Item" not in response:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Profile not found"}),
            }

        profile = response["Item"]
        # DynamoDB 내부 필드 제거
        profile.pop("user_id", None)
        profile.pop("updated_at", None)

        metrics.add_metric(name="ProfileGet", unit=MetricUnit.Count, value=1)

        return {"statusCode": 200, "headers": headers, "body": json.dumps(profile)}

    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise


@tracer.capture_method
def _update_profile(user_id: str, body: str, headers: dict):
    """프로필 업데이트"""
    try:
        # 요청 본문 파싱
        profile_data = json.loads(body)

        # 입력 검증
        try:
            jsonschema.validate(profile_data, USER_PROFILE_SCHEMA)
        except jsonschema.ValidationError as e:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": f"Invalid profile data: {e.message}"}),
            }

        # 입력 sanitization
        sanitized_profile = {}
        for key, value in profile_data.items():
            if isinstance(value, str):
                sanitized_profile[key] = sanitize_input(value)
            else:
                sanitized_profile[key] = value

        # DynamoDB 업데이트
        sanitized_profile["user_id"] = user_id
        sanitized_profile["updated_at"] = datetime.utcnow().isoformat()

        table.put_item(Item=sanitized_profile)

        # 응답용 데이터 정리
        response_profile = sanitized_profile.copy()
        response_profile.pop("user_id", None)
        response_profile.pop("updated_at", None)

        metrics.add_metric(name="ProfileUpdate", unit=MetricUnit.Count, value=1)
        logger.info(f"Profile updated for user: {user_id}")

        return {"statusCode": 200, "headers": headers, "body": json.dumps(response_profile)}

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid JSON"}),
        }
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise
