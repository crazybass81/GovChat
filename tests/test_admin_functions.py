"""
관리자 기능 테스트
"""

import pytest
from unittest.mock import Mock, patch
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../infra/src'))

from functions.admin_handler import handler, _create_project, _update_project, _delete_project


class TestAdminFunctions:
    """관리자 기능 테스트"""
    
    @patch('functions.admin_handler.verify_admin_token')
    @patch('functions.admin_handler.projects_table')
    def test_create_project_success(self, mock_table, mock_verify):
        """프로젝트 생성 성공 테스트"""
        mock_verify.return_value = {
            "valid": True,
            "user": {"email": "admin@test.com", "role": "admin"}
        }
        mock_table.put_item.return_value = {}
        
        event = {
            "httpMethod": "POST",
            "resource": "/admin/projects",
            "headers": {"Authorization": "Bearer valid-token"},
            "body": json.dumps({
                "title": "테스트 프로젝트",
                "description": "테스트 설명",
                "agency": "테스트 기관"
            })
        }
        
        response = handler(event, {})
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert "성공적으로 생성" in body["message"]
    
    @patch('functions.admin_handler.verify_admin_token')
    def test_create_project_unauthorized(self, mock_verify):
        """권한 없는 프로젝트 생성 시도 테스트"""
        mock_verify.return_value = {"valid": False, "error": "권한 없음"}
        
        event = {
            "httpMethod": "POST",
            "resource": "/admin/projects",
            "headers": {"Authorization": "Bearer invalid-token"},
            "body": json.dumps({"title": "테스트"})
        }
        
        response = handler(event, {})
        
        assert response["statusCode"] == 403
    
    @patch('functions.admin_handler.verify_admin_token')
    @patch('functions.admin_handler.projects_table')
    def test_update_project_success(self, mock_table, mock_verify):
        """프로젝트 수정 성공 테스트"""
        mock_verify.return_value = {
            "valid": True,
            "user": {"email": "admin@test.com", "role": "admin"}
        }
        mock_table.get_item.return_value = {"Item": {"project_id": "test-id"}}
        mock_table.update_item.return_value = {}
        
        event = {
            "httpMethod": "PUT",
            "resource": "/admin/projects/{id}",
            "pathParameters": {"id": "test-id"},
            "headers": {"Authorization": "Bearer valid-token"},
            "body": json.dumps({"title": "수정된 제목"})
        }
        
        response = handler(event, {})
        
        assert response["statusCode"] == 200
    
    @patch('functions.admin_handler.verify_admin_token')
    @patch('functions.admin_handler.projects_table')
    def test_delete_project_success(self, mock_table, mock_verify):
        """프로젝트 삭제 성공 테스트"""
        mock_verify.return_value = {
            "valid": True,
            "user": {"email": "admin@test.com", "role": "admin"}
        }
        mock_table.get_item.return_value = {"Item": {"project_id": "test-id", "title": "테스트"}}
        mock_table.update_item.return_value = {}
        
        event = {
            "httpMethod": "DELETE",
            "resource": "/admin/projects/{id}",
            "pathParameters": {"id": "test-id"},
            "headers": {"Authorization": "Bearer valid-token"}
        }
        
        response = handler(event, {})
        
        assert response["statusCode"] == 200
        # 소프트 삭제 확인
        mock_table.update_item.assert_called_once()
    
    @patch('functions.admin_handler.verify_admin_token')
    @patch('functions.admin_handler.admin_logs_table')
    def test_get_admin_logs(self, mock_logs_table, mock_verify):
        """관리자 로그 조회 테스트"""
        mock_verify.return_value = {
            "valid": True,
            "user": {"email": "admin@test.com", "role": "admin"}
        }
        mock_logs_table.scan.return_value = {
            "Items": [
                {
                    "log_id": "log1",
                    "admin_email": "admin@test.com",
                    "action": "CREATE_PROJECT",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
        }
        
        event = {
            "httpMethod": "GET",
            "resource": "/admin/logs",
            "headers": {"Authorization": "Bearer valid-token"},
            "queryStringParameters": {"limit": "10"}
        }
        
        response = handler(event, {})
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["logs"]) == 1
    
    def test_input_sanitization(self):
        """입력 데이터 정제 테스트"""
        from common.xss_protection import sanitize_input
        
        # XSS 공격 시도
        malicious_input = "<script>alert('xss')</script>테스트"
        sanitized = sanitize_input(malicious_input)
        
        assert "<script>" not in sanitized
        assert "테스트" in sanitized