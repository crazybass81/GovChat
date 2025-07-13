"""Unit tests for policy handler"""
import json
import pytest
from unittest.mock import patch, MagicMock
from src.functions.policy_handler import lambda_handler


class TestPolicyHandler:
    """Test cases for policy handler"""
    
    @patch('boto3.resource')
    def test_create_policy_success(self, mock_boto3):
        """Test successful policy creation"""
        mock_table = MagicMock()
        mock_table.put_item.return_value = {}
        mock_boto3.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                'title': 'Test Policy',
                'description': 'Test policy description',
                'eligibility_criteria': {
                    'age_min': 18,
                    'income_max': 50000
                }
            })
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 201
        response_body = json.loads(result['body'])
        assert response_body['message'] == 'Policy created successfully'
        
    @patch('boto3.resource')
    def test_get_policy_success(self, mock_boto3):
        """Test successful policy retrieval"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'policy_id': 'policy123',
                'title': 'Test Policy',
                'status': 'draft'
            }
        }
        mock_boto3.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'pathParameters': {'policy_id': 'policy123'}
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['title'] == 'Test Policy'
        
    @patch('boto3.resource')
    def test_publish_policy_already_published(self, mock_boto3):
        """Test publishing already published policy returns error"""
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'policy_id': 'policy123',
                'status': 'published'
            }
        }
        mock_boto3.return_value.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'PUT',
            'pathParameters': {'policy_id': 'policy123'},
            'body': json.dumps({'action': 'publish'})
        }
        
        result = lambda_handler(event, {})
        
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'already published' in response_body['error']