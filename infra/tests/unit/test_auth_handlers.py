"""Unit tests for authentication handlers"""
import json
import pytest
from unittest.mock import patch, MagicMock
from src.functions.admin_auth_handler import lambda_handler as admin_auth_handler
from src.functions.user_auth_handler import lambda_handler as user_auth_handler


class TestAdminAuthHandler:
    """Test cases for admin authentication handler"""
    
    @patch('boto3.resource')
    def test_admin_login_success(self, mock_boto3):
        """Test successful admin login"""
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'admin_id': 'admin123',
                'password_hash': 'hashed_password',
                'role': 'admin'
            }
        }
        mock_boto3.return_value.Table.return_value = mock_table
        
        event = {
            'body': json.dumps({
                'admin_id': 'admin123',
                'password': 'correct_password'
            })
        }
        
        with patch('bcrypt.checkpw', return_value=True):
            result = admin_auth_handler(event, {})
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'token' in response_body
        
    @patch('boto3.resource')
    def test_admin_login_invalid_credentials(self, mock_boto3):
        """Test admin login with invalid credentials"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_boto3.return_value.Table.return_value = mock_table
        
        event = {
            'body': json.dumps({
                'admin_id': 'invalid_admin',
                'password': 'wrong_password'
            })
        }
        
        result = admin_auth_handler(event, {})
        
        assert result['statusCode'] == 401
        response_body = json.loads(result['body'])
        assert 'error' in response_body


class TestUserAuthHandler:
    """Test cases for user authentication handler"""
    
    @patch('boto3.resource')
    def test_user_signup_success(self, mock_boto3):
        """Test successful user signup"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # User doesn't exist
        mock_table.put_item.return_value = {}
        mock_boto3.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'POST',
            'path': '/auth/user/signup',
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'secure_password',
                'name': 'Test User'
            })
        }
        
        result = user_auth_handler(event, {})
        
        assert result['statusCode'] == 201
        response_body = json.loads(result['body'])
        assert response_body['message'] == 'User created successfully'
        
    @patch('boto3.resource')
    def test_user_login_success(self, mock_boto3):
        """Test successful user login"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'email': 'test@example.com',
                'password_hash': 'hashed_password',
                'name': 'Test User'
            }
        }
        mock_boto3.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'POST',
            'path': '/auth/user/login',
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'correct_password'
            })
        }
        
        with patch('bcrypt.checkpw', return_value=True):
            result = user_auth_handler(event, {})
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'token' in response_body