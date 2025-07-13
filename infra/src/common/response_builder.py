"""
표준 응답 형식 빌더
"""

import json
from typing import Any, Dict, Optional


def build_success_response(data: Any, status_code: int = 200) -> Dict:
    """성공 응답 생성"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data, ensure_ascii=False)
    }


def build_error_response(error_message: str, status_code: int = 500) -> Dict:
    """에러 응답 생성"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        },
        'body': json.dumps({'error': error_message}, ensure_ascii=False)
    }


def build_paginated_response(items: list, total: int, page: int = 1, 
                           page_size: int = 20, **kwargs) -> Dict:
    """페이지네이션 응답 생성"""
    data = {
        'items': items,
        'pagination': {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    }
    data.update(kwargs)
    return build_success_response(data)


def build_chat_response(message: str, response_type: str = "text", 
                       **kwargs) -> Dict:
    """챗봇 응답 생성"""
    data = {
        'message': message,
        'type': response_type,
        'timestamp': kwargs.get('timestamp'),
        **kwargs
    }
    return build_success_response(data)