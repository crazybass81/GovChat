"""
강화된 인증 시스템 테스트
"""

import pytest
import bcrypt
import jwt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../infra/src'))

from functions.user_auth_handler import handler, _generate_jwt
from common.api_auth import verify_token, verify_admin_token


class TestAuthEnhanced:
    """강화된 인증 테스트"""
    
    def test_bcrypt_password_hashing(self):
        """bcrypt 해시 테스트"""
        password = "test123!@#"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        
        assert bcrypt.checkpw(password.encode('utf-8'), hashed)
        assert not bcrypt.checkpw("wrong".encode('utf-8'), hashed)
    
    @patch('functions.user_auth_handler.user_table')
    @patch('functions.user_auth_handler.boto3')
    def test_signup_with_bcrypt(self, mock_boto3, mock_table):
        """bcrypt를 사용한 회원가입 테스트"""
        mock_table.get_item.return_value = {}
        mock_table.put_item.return_value = {}
        
        event = {
            "httpMethod": "POST",
            "resource": "/auth/user/signup",
            "body": '{"email": "test@test.com", "password": "test123", "name": "Test User"}'
        }
        
        response = handler(event, {})
        
        assert response["statusCode"] == 201
        mock_table.put_item.assert_called_once()
    
    def test_jwt_token_expiry(self):
        """JWT 토큰 만료 시간 테스트"""
        token = _generate_jwt("test@test.com", "user")
        
        with patch('functions.user_auth_handler.ssm') as mock_ssm:
            mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-secret'}}
            
            decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])
            exp_time = datetime.fromtimestamp(decoded['exp'])
            now = datetime.utcnow()
            
            # 15분 만료 확인
            assert (exp_time - now).total_seconds() <= 900
    
    @patch('common.api_auth.ssm')
    def test_token_verification(self, mock_ssm):
        """토큰 검증 테스트"""
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-secret'}}
        
        # 유효한 토큰
        payload = {
            "email": "test@test.com",
            "role": "user",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {token}"}
        result = verify_token(headers)
        
        assert result["valid"] is True
        assert result["user"]["email"] == "test@test.com"
    
    @patch('common.api_auth.ssm')
    def test_admin_token_verification(self, mock_ssm):
        """관리자 토큰 검증 테스트"""
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-secret'}}
        
        # 관리자 토큰
        payload = {
            "email": "admin@test.com",
            "role": "admin",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }
        token = jwt.encode(payload, "test-secret", algorithm="HS256")
        
        headers = {"Authorization": f"Bearer {token}"}
        result = verify_admin_token(headers)
        
        assert result["valid"] is True
        
        # 일반 사용자 토큰으로 관리자 검증 시도
        payload["role"] = "user"
        user_token = jwt.encode(payload, "test-secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {user_token}"}
        result = verify_admin_token(headers)
        
        assert result["valid"] is False
    
    def test_rate_limiting(self):
        """Rate limiting 테스트"""
        from common.api_auth import rate_limit_check
        
        with patch('common.api_auth.dynamodb') as mock_db:
            mock_table = Mock()
            mock_db.Table.return_value = mock_table
            
            # 첫 번째 요청
            mock_table.query.return_value = {"Items": []}
            result = rate_limit_check("test-client", max_requests=2, window_minutes=15)
            assert result["allowed"] is True
            
            # 한계 초과 요청
            mock_table.query.return_value = {"Items": [1, 2]}
            result = rate_limit_check("test-client", max_requests=2, window_minutes=15)
            assert result["allowed"] is False