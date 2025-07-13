"""Simple function tests to improve coverage"""
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from test_utils import (
    validate_email, 
    hash_password, 
    verify_password,
    validate_policy_data,
    ResponseBuilder
)


def test_email_validation():
    """Test email validation function"""
    assert validate_email('test@example.com') is True
    assert validate_email('invalid-email') is False


def test_password_functions():
    """Test password hashing and verification"""
    password = 'test123'
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password('wrong', hashed) is False


def test_policy_validation():
    """Test policy data validation"""
    valid_policy = {
        'title': 'Test',
        'description': 'Test desc',
        'eligibility_criteria': {}
    }
    assert validate_policy_data(valid_policy) is True
    
    invalid_policy = {'title': 'Test'}
    assert validate_policy_data(invalid_policy) is False


def test_response_builder():
    """Test response builder"""
    success_resp = ResponseBuilder.success({'data': 'test'})
    assert success_resp['statusCode'] == 200
    assert success_resp['body']['data'] == 'test'
    
    error_resp = ResponseBuilder.error('Error message')
    assert error_resp['statusCode'] == 400
    assert error_resp['body']['error'] == 'Error message'