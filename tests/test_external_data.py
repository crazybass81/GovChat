"""
외부 데이터 연동 테스트
"""

import pytest
from unittest.mock import Mock, patch
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../infra/src'))

from functions.external_data_sync_handler import handler, _fetch_external_policies, _upsert_policy


class TestExternalData:
    """외부 데이터 연동 테스트"""
    
    @patch('functions.external_data_sync_handler.requests')
    @patch('functions.external_data_sync_handler.ssm')
    def test_fetch_external_policies_success(self, mock_ssm, mock_requests):
        """외부 API 데이터 가져오기 성공 테스트"""
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-api-key'}}
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": {
                "header": {"resultCode": "00"},
                "body": {
                    "items": [
                        {
                            "policyId": "P001",
                            "policyName": "청년창업지원",
                            "organName": "중소벤처기업부"
                        }
                    ]
                }
            }
        }
        mock_requests.get.return_value = mock_response
        
        result = _fetch_external_policies("청년")
        
        assert len(result) == 1
        assert result[0]["policyId"] == "P001"
    
    @patch('functions.external_data_sync_handler.requests')
    @patch('functions.external_data_sync_handler.ssm')
    def test_fetch_external_policies_api_error(self, mock_ssm, mock_requests):
        """외부 API 오류 테스트"""
        mock_ssm.get_parameter.return_value = {'Parameter': {'Value': 'test-api-key'}}
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": {
                "header": {"resultCode": "99", "resultMsg": "API Error"}
            }
        }
        mock_requests.get.return_value = mock_response
        
        with pytest.raises(Exception, match="API Error"):
            _fetch_external_policies("청년")
    
    @patch('functions.external_data_sync_handler.projects_table')
    def test_upsert_policy_insert(self, mock_table):
        """정책 데이터 삽입 테스트"""
        mock_table.get_item.return_value = {}
        mock_table.put_item.return_value = {}
        
        policy_data = {
            "policyId": "P001",
            "policyName": "청년창업지원",
            "organName": "중소벤처기업부"
        }
        
        result = _upsert_policy(policy_data)
        
        assert result == "insert"
        mock_table.put_item.assert_called_once()
    
    @patch('functions.external_data_sync_handler.projects_table')
    def test_upsert_policy_update(self, mock_table):
        """정책 데이터 업데이트 테스트"""
        mock_table.get_item.return_value = {"Item": {"policy_external_id": "P001"}}
        mock_table.update_item.return_value = {}
        
        policy_data = {
            "policyId": "P001",
            "policyName": "청년창업지원 수정",
            "organName": "중소벤처기업부"
        }
        
        result = _upsert_policy(policy_data)
        
        assert result == "update"
        mock_table.update_item.assert_called_once()
    
    @patch('functions.external_data_sync_handler._sync_policies_by_keyword')
    def test_scheduled_sync(self, mock_sync):
        """정기 동기화 테스트"""
        mock_sync.return_value = {
            "total": 5,
            "inserted": 3,
            "updated": 2,
            "errors": []
        }
        
        event = {"source": "aws.events"}
        response = handler(event, {})
        
        assert response["statusCode"] == 200
        assert mock_sync.call_count == 4  # 4개 키워드
    
    @patch('functions.external_data_sync_handler._sync_policies_by_keyword')
    def test_manual_sync(self, mock_sync):
        """수동 동기화 테스트"""
        mock_sync.return_value = {
            "total": 3,
            "inserted": 2,
            "updated": 1,
            "errors": []
        }
        
        event = {
            "httpMethod": "POST",
            "resource": "/admin/sync-policies"
        }
        response = handler(event, {})
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "동기화가 완료되었습니다" in body["message"]