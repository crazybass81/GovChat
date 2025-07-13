"""
통합 로깅 설정
"""

import os
from aws_lambda_powertools import Logger

def setup_logger(name: str) -> Logger:
    """
    표준화된 로거 설정
    
    Args:
        name: 로거 이름
    
    Returns:
        설정된 Logger 인스턴스
    """
    logger = Logger(
        service=name,
        level=os.getenv("LOG_LEVEL", "INFO"),
        sample_rate=float(os.getenv("LOG_SAMPLE_RATE", "0.1")),
        log_uncaught_exceptions=True
    )
    
    return logger

def log_request(logger: Logger, event: dict, context: dict = None):
    """요청 로깅"""
    logger.info(
        "Request received",
        extra={
            "method": event.get("httpMethod"),
            "path": event.get("path"),
            "query_params": event.get("queryStringParameters"),
            "headers": {k: v for k, v in event.get("headers", {}).items() 
                      if k.lower() not in ['authorization', 'cookie']},
            "request_id": context.aws_request_id if context else None
        }
    )

def log_response(logger: Logger, response: dict, duration_ms: float = None):
    """응답 로깅"""
    logger.info(
        "Response sent",
        extra={
            "status_code": response.get("statusCode"),
            "duration_ms": duration_ms
        }
    )