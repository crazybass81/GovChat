"""
통합 에러 처리
"""

import json
import functools
from aws_lambda_powertools import Logger

logger = Logger()


def handle_lambda_error(func):
    """Lambda 함수 에러 처리 데코레이터"""
    @functools.wraps(func)
    def wrapper(event, context):
        try:
            return func(event, context)
        except Exception as e:
            logger.error("Lambda error", extra={
                "error": str(e),
                "function": func.__name__,
                "event": event
            })
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Internal server error'})
            }
    return wrapper


def handle_validation_error(message: str):
    """입력 검증 에러 응답"""
    return {
        'statusCode': 400,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }


def handle_auth_error(message: str = "Unauthorized"):
    """인증 에러 응답"""
    return {
        'statusCode': 401,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }


def handle_forbidden_error(message: str = "Forbidden"):
    """권한 에러 응답"""
    return {
        'statusCode': 403,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }


def handle_not_found_error(message: str = "Not found"):
    """리소스 없음 에러 응답"""
    return {
        'statusCode': 404,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': message})
    }