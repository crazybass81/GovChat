"""
표준 응답 형식 빌더
"""

import json
from typing import Any, Dict, Optional

def build_response(
    data: Any,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    표준화된 Lambda 응답 생성
    
    Args:
        data: 응답 데이터
        status_code: HTTP 상태 코드
        headers: 추가 헤더
    
    Returns:
        Lambda 응답 형식
    """
    default_headers = {
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(data, ensure_ascii=False)
    }

def build_success_response(data: Any, message: str = "성공") -> Dict[str, Any]:
    """성공 응답 생성"""
    return build_response({
        "success": True,
        "message": message,
        "data": data
    })

def build_error_response(error: str, status_code: int = 400) -> Dict[str, Any]:
    """에러 응답 생성"""
    return build_response({
        "success": False,
        "error": error
    }, status_code)

def build_paginated_response(
    items: list,
    total: int,
    page: int = 1,
    limit: int = 10
) -> Dict[str, Any]:
    """페이지네이션 응답 생성"""
    return build_response({
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    })