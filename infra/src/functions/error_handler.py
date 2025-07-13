"""
통합 에러 처리 모듈
"""

import json
import traceback
from aws_lambda_powertools import Logger
from response_builder import build_response

logger = Logger()

def handle_error(error: Exception, user_message: str = "처리 중 오류가 발생했습니다", status_code: int = 500) -> dict:
    """
    통합 에러 처리
    
    Args:
        error: 발생한 예외
        user_message: 사용자에게 표시할 메시지
        status_code: HTTP 상태 코드
    
    Returns:
        표준화된 에러 응답
    """
    error_id = f"ERR_{hash(str(error)) % 10000:04d}"
    
    logger.error(
        "Lambda function error",
        extra={
            "error_id": error_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc()
        }
    )
    
    return build_response(
        {
            "error": user_message,
            "error_id": error_id
        },
        status_code
    )

def handle_validation_error(field: str, message: str = None) -> dict:
    """입력 검증 에러 처리"""
    error_message = message or f"{field}이(가) 올바르지 않습니다"
    return build_response(
        {
            "error": error_message,
            "field": field
        },
        400
    )

def handle_not_found_error(resource: str = "리소스") -> dict:
    """404 에러 처리"""
    return build_response(
        {"error": f"{resource}를 찾을 수 없습니다"},
        404
    )

def handle_auth_error(message: str = "인증이 필요합니다") -> dict:
    """인증 에러 처리"""
    return build_response(
        {"error": message},
        401
    )

def handle_permission_error(message: str = "권한이 없습니다") -> dict:
    """권한 에러 처리"""
    return build_response(
        {"error": message},
        403
    )