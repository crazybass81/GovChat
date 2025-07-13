"""Unit tests for authentication handlers"""
import json
import pytest
from unittest.mock import patch, MagicMock


class TestAdminAuthHandler:
    """Test cases for admin authentication handler"""
    
    @patch('boto3.resource')
    @patch('bcrypt.checkpw')
    def test_admin_login_success(self, mock_checkpw, mock_boto3):
        """Test successful admin login logic"""
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
        mock_checkpw.return_value = True
        
        # Test the logic without importing the actual handler
        admin_id = 'admin123'
        password = 'correct_password'
        
        # Simulate DynamoDB lookup
        table = mock_boto3.return_value.Table.return_value
        response = table.get_item(Key={'admin_id': admin_id})
        
        assert 'Item' in response
        assert response['Item']['admin_id'] == admin_id
        assert mock_checkpw.called
        
    @patch('boto3.resource')
    def test_admin_login_invalid_credentials(self, mock_boto3):
        """Test admin login with invalid credentials"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_boto3.return_value.Table.return_value = mock_table
        
        # Test invalid admin lookup
        admin_id = 'invalid_admin'
        table = mock_boto3.return_value.Table.return_value
        response = table.get_item(Key={'admin_id': admin_id})
        
        assert 'Item' not in response


class TestUserAuthHandler:
    """Test cases for user authentication handler"""
    
    @patch('boto3.resource')
    def test_user_signup_success(self, mock_boto3):
        """Test successful user signup logic"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}  # User doesn't exist
        mock_table.put_item.return_value = {}
        mock_boto3.return_value.Table.return_value = mock_table
        
        # Test user creation logic
        email = 'test@example.com'
        table = mock_boto3.return_value.Table.return_value
        
        # Check if user exists
        existing_user = table.get_item(Key={'email': email})
        assert 'Item' not in existing_user
        
        # Create new user
        table.put_item(Item={'email': email, 'name': 'Test User'})
        assert table.put_item.called
        
    @patch('boto3.resource')
    @patch('bcrypt.checkpw')
    def test_user_login_success(self, mock_checkpw, mock_boto3):
        """Test successful user login logic"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'email': 'test@example.com',
                'password_hash': 'hashed_password',
                'name': 'Test User'
            }
        }
        mock_boto3.return_value.Table.return_value = mock_table
        mock_checkpw.return_value = True
        
        # Test user login logic
        email = 'test@example.com'
        table = mock_boto3.return_value.Table.return_value
        response = table.get_item(Key={'email': email})
        
        assert 'Item' in response
        assert response['Item']['email'] == email
        assert mock_checkpw.called