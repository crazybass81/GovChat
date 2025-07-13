"""Unit tests for utility functions"""
import pytest
from src.test_utils import (
    validate_email, 
    hash_password, 
    verify_password,
    validate_policy_data,
    ResponseBuilder
)


class TestEmailValidation:
    """Test email validation"""
    
    def test_valid_email(self):
        """Test valid email formats"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.kr',
            'admin+tag@company.org'
        ]
        for email in valid_emails:
            assert validate_email(email) is True
    
    def test_invalid_email(self):
        """Test invalid email formats"""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user@domain',
            ''
        ]
        for email in invalid_emails:
            assert validate_email(email) is False


class TestPasswordHashing:
    """Test password hashing functions"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = 'test_password'
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_verify_password(self):
        """Test password verification"""
        password = 'test_password'
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password('wrong_password', hashed) is False


class TestPolicyValidation:
    """Test policy data validation"""
    
    def test_valid_policy_data(self):
        """Test valid policy data"""
        valid_policy = {
            'title': 'Test Policy',
            'description': 'Test description',
            'eligibility_criteria': {'age_min': 18}
        }
        assert validate_policy_data(valid_policy) is True
    
    def test_invalid_policy_data(self):
        """Test invalid policy data"""
        invalid_policies = [
            {'title': 'Test'},  # Missing fields
            {'description': 'Test'},  # Missing fields
            {},  # Empty
        ]
        for policy in invalid_policies:
            assert validate_policy_data(policy) is False


class TestResponseBuilder:
    """Test response builder"""
    
    def test_success_response(self):
        """Test success response building"""
        data = {'message': 'Success'}
        response = ResponseBuilder.success(data)
        
        assert response['statusCode'] == 200
        assert response['body'] == data
        assert 'X-Frame-Options' in response['headers']
    
    def test_error_response(self):
        """Test error response building"""
        message = 'Error occurred'
        response = ResponseBuilder.error(message, 400)
        
        assert response['statusCode'] == 400
        assert response['body']['error'] == message
        assert 'X-Content-Type-Options' in response['headers']