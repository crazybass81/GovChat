"""Pytest fixtures for AWS service mocking"""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table with common operations"""
    with patch('boto3.resource') as mock_boto3:
        mock_table = MagicMock()
        mock_boto3.return_value.Table.return_value = mock_table
        
        # Default responses
        mock_table.get_item.return_value = {}
        mock_table.put_item.return_value = {}
        mock_table.update_item.return_value = {}
        mock_table.delete_item.return_value = {}
        mock_table.scan.return_value = {'Items': []}
        mock_table.query.return_value = {'Items': []}
        
        yield mock_table


@pytest.fixture
def mock_s3_client():
    """Mock S3 client with common operations"""
    with patch('boto3.client') as mock_boto3:
        mock_s3 = MagicMock()
        mock_boto3.return_value = mock_s3
        
        # Default responses
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'{"test": "data"}')
        }
        mock_s3.put_object.return_value = {}
        mock_s3.delete_object.return_value = {}
        mock_s3.list_objects_v2.return_value = {'Contents': []}
        
        yield mock_s3


@pytest.fixture
def mock_ssm_client():
    """Mock SSM client for parameter store"""
    with patch('boto3.client') as mock_boto3:
        mock_ssm = MagicMock()
        mock_boto3.return_value = mock_ssm
        
        # Default parameter responses
        mock_ssm.get_parameter.return_value = {
            'Parameter': {'Value': 'mock-value'}
        }
        mock_ssm.get_parameters.return_value = {
            'Parameters': [{'Name': 'test', 'Value': 'mock-value'}]
        }
        
        yield mock_ssm


@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client"""
    with patch('opensearchpy.OpenSearch') as mock_opensearch:
        mock_client = MagicMock()
        mock_opensearch.return_value = mock_client
        
        # Default search responses
        mock_client.search.return_value = {
            'hits': {
                'total': {'value': 0},
                'hits': []
            }
        }
        mock_client.index.return_value = {'result': 'created'}
        mock_client.delete.return_value = {'result': 'deleted'}
        
        yield mock_client


@pytest.fixture
def mock_all_aws_services(mock_dynamodb_table, mock_s3_client, mock_ssm_client):
    """Convenience fixture that mocks all common AWS services"""
    return {
        'dynamodb': mock_dynamodb_table,
        's3': mock_s3_client,
        'ssm': mock_ssm_client
    }