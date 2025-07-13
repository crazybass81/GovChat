"""
B1: 사용자 인증 API Lambda 핸들러
"""

import hashlib
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

dynamodb = boto3.resource("dynamodb")
user_table = dynamodb.Table("UserTable")


@tracer.capture_lambda_handler
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics
def handler(event, context):
    """사용자 인증 핸들러"""
    try:
        headers = secure_headers()

        if event["httpMethod"] == "OPTIONS":
            return {"statusCode": 200, "headers": headers, "body": ""}

        path = event["resource"]
        method = event["httpMethod"]

        if method == "POST" and path == "/auth/user/signup":
            return _signup(event.get("body", "{}"), headers)
        elif method == "POST" and path == "/auth/user/login":
            return _login(event.get("body", "{}"), headers)
        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Not found"}),
            }

    except Exception as e:
        logger.error(f"User auth error: {e}")
        metrics.add_metric(name="AuthError", unit=MetricUnit.Count, value=1)
        return {
            "statusCode": 500,
            "headers": secure_headers(),
            "body": json.dumps({"error": "Internal server error"}),
        }


@tracer.capture_method
def _signup(body: str, headers: dict):
    """사용자 회원가입"""
    try:
        data = json.loads(body)

        name = sanitize_input(data.get("name", ""))
        phone = sanitize_input(data.get("phone", ""))
        email = sanitize_input(data.get("email", ""))
        password = data.get("password", "")

        if not all([name, phone, email, password]):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "All fields required"}),
            }

        # 이메일 중복 확인
        try:
            existing = user_table.get_item(Key={"email": email})
            if "Item" in existing:
                return {
                    "statusCode": 409,
                    "headers": headers,
                    "body": json.dumps({"error": "Email already exists"}),
                }
        except Exception:
            pass

        # 비밀번호 해시
        password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), b"salt", 100000).hex()

        # 사용자 생성
        user_item = {
            "email": email,
            "name": name,
            "phone": phone,
            "provider": "local",
            "password_hash": password_hash,
            "created_at": datetime.utcnow().isoformat(),
        }

        user_table.put_item(Item=user_item)

        metrics.add_metric(name="UserSignup", unit=MetricUnit.Count, value=1)
        logger.info(f"User signup successful: {email}")

        return {
            "statusCode": 201,
            "headers": headers,
            "body": json.dumps({"message": "User created successfully"}),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid JSON"}),
        }
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise


@tracer.capture_method
def _login(body: str, headers: dict):
    """사용자 로그인"""
    try:
        data = json.loads(body)

        email = sanitize_input(data.get("email", ""))
        password = data.get("password", "")

        if not email or not password:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Email and password required"}),
            }

        # 사용자 조회
        try:
            user_response = user_table.get_item(Key={"email": email})
            if "Item" not in user_response:
                metrics.add_metric(name="LoginFailure", unit=MetricUnit.Count, value=1)
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": "Invalid credentials"}),
                }

            user = user_response["Item"]

            # 비밀번호 검증
            password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), b"salt", 100000).hex()
            if user.get("password_hash") != password_hash:
                metrics.add_metric(name="LoginFailure", unit=MetricUnit.Count, value=1)
                return {
                    "statusCode": 401,
                    "headers": headers,
                    "body": json.dumps({"error": "Invalid credentials"}),
                }

        except Exception as e:
            logger.error(f"User lookup error: {e}")
            return {
                "statusCode": 401,
                "headers": headers,
                "body": json.dumps({"error": "Invalid credentials"}),
            }

        # JWT 생성
        jwt_token = _generate_jwt(email, "user")

        # HTTP-Only 쿠키 설정
        cookie_header = (
            f"access_token={jwt_token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=3600"
        )
        headers["Set-Cookie"] = cookie_header

        metrics.add_metric(name="LoginSuccess", unit=MetricUnit.Count, value=1)
        logger.info(f"User login successful: {email}")

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(
                {
                    "message": "Login successful",
                    "user": {"email": email, "name": user.get("name"), "role": "user"},
                }
            ),
        }

    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid JSON"}),
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise


def _generate_jwt(email: str, role: str) -> str:
    """JWT 토큰 생성"""
    payload = {
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }

    # TODO: KMS에서 키 가져오기
    secret_key = "temp-secret-key"

    return jwt.encode(payload, secret_key, algorithm="HS256")
