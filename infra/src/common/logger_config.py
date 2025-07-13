"""
통합 로깅 설정
"""

from aws_lambda_powertools import Logger
from typing import Optional


def get_logger(service_name: str, level: str = "INFO") -> Logger:
    """통합 로거 생성"""
    return Logger(
        service=service_name,
        level=level,
        log_uncaught_exceptions=True,
        serialize_stacktrace=True
    )


def log_request(logger: Logger, event: dict, context: Optional[object] = None):
    """요청 로깅"""
    logger.info("Request received", extra={
        "request_id": getattr(context, 'aws_request_id', None) if context else None,
        "event_keys": list(event.keys()) if isinstance(event, dict) else None
    })


def log_response(logger: Logger, response: dict, context: Optional[object] = None):
    """응답 로깅"""
    logger.info("Response sent", extra={
        "request_id": getattr(context, 'aws_request_id', None) if context else None,
        "status_code": response.get('statusCode'),
        "response_size": len(str(response))
    })


def log_error(logger: Logger, error: Exception, context: Optional[object] = None):
    """에러 로깅"""
    logger.error("Error occurred", extra={
        "request_id": getattr(context, 'aws_request_id', None) if context else None,
        "error_type": type(error).__name__,
        "error_message": str(error)
    })