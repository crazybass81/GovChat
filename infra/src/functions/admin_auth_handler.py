"""
A1: 관리자 인증 API Lambda 핸들러
"""

import json
from datetime import datetime, timedelta

import boto3
import jwt
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from common.xss_protection import sanitize_input, secure_headers

logger = Logger()
tracer = Tracer()
metrics = Metrics()

ssm = boto3.client("ssm")
kms = boto3.client("kms")


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def handler(event, context):
    """관리자 인증 핸들러"""
    try:
        # CORS 및 보안 헤더 설정
        headers = secure_headers()

        if event["httpMethod"] == "OPTIONS":
            return {"statusCode": 200, "headers": headers, "body": ""}

        # 요청 본문 파싱 및 검증
        body = json.loads(event.get("body", "{}"))
        email = sanitize_input(body.get("email", ""))
        token = sanitize_input(body.get("token", ""))

        if not email or not token:
            metrics.add_metric(name="AuthFailure", unit=MetricUnit.Count, value=1)
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Email and token required"}),
            }

        # 관리자 허용 목록 확인
        try:
            admin_allowlist = ssm.get_parameter(
                Name="/govchat/admin/allowlist", WithDecryption=True
            )["Parameter"]["Value"]
            allowed_emails = json.loads(admin_allowlist)
        except Exception as e:
            logger.error(f"Failed to get admin allowlist: {e}")
            return {
                "statusCode": 500,
                "headers": headers,
                "body": json.dumps({"error": "Internal server error"}),
            }

        # 이메일 검증
        if email not in allowed_emails:
            metrics.add_metric(name="AuthFailure", unit=MetricUnit.Count, value=1)
            logger.warning(f"Unauthorized admin login attempt: {email}")
            return {
                "statusCode": 401,
                "headers": headers,
                "body": json.dumps({"error": "Unauthorized"}),
            }

        # 토큰 검증 (실제 구현에서는 SSO 토큰 검증)
        if not _verify_admin_token(token, email):
            metrics.add_metric(name="AuthFailure", unit=MetricUnit.Count, value=1)
            return {
                "statusCode": 401,
                "headers": headers,
                "body": json.dumps({"error": "Invalid token"}),
            }

        # JWT 생성
        jwt_token = _generate_jwt(email, "admin")

        # HTTP-Only 쿠키 설정
        cookie_header = (
            f"access_token={jwt_token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=3600"
        )
        headers["Set-Cookie"] = cookie_header

        metrics.add_metric(name="AuthSuccess", unit=MetricUnit.Count, value=1)
        logger.info(f"Admin login successful: {email}")

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(
                {"message": "Login successful", "user": {"email": email, "role": "admin"}}
            ),
        }

    except Exception as e:
        logger.error(f"Admin auth error: {e}")
        metrics.add_metric(name="AuthError", unit=MetricUnit.Count, value=1)
        return {
            "statusCode": 500,
            "headers": secure_headers(),
            "body": json.dumps({"error": "Internal server error"}),
        }


def _verify_admin_token(token: str, email: str) -> bool:
    """관리자 토큰 검증 (실제 구현에서는 SSO 연동)"""
    # TODO: 실제 SSO 토큰 검증 로직 구현
    return len(token) > 10  # 임시 검증


def _generate_jwt(email: str, role: str) -> str:
    """JWT 토큰 생성"""
    payload = {
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }

    # KMS로 서명 키 관리 (실제 구현에서는 KMS CMK 사용)
    secret_key = "temp-secret-key"  # TODO: KMS에서 키 가져오기

    return jwt.encode(payload, secret_key, algorithm="HS256")
