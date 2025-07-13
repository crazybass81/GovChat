"""
정부 데이터 API 클라이언트
data.go.kr API 호출 및 키 관리
"""

from typing import Dict

import boto3
import requests
from aws_lambda_powertools import Logger

logger = Logger()


class DataGoKrClient:
    """data.go.kr API 클라이언트"""

    def __init__(self):
        self.base_url = "https://www.data.go.kr/api/15000001"
        self.api_key = None
        self._load_api_key()

    def _load_api_key(self):
        """Secrets Manager에서 API 키 로드"""
        try:
            secrets_client = boto3.client("secretsmanager")
            response = secrets_client.get_secret_value(SecretId="gov-support/data-go-kr-api-key")
            self.api_key = response["SecretString"]
            logger.info("Government API key loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load API key: {e}")
            raise

    def search_policies(self, keyword: str, page: int = 1, per_page: int = 10) -> Dict:
        """정책 검색"""
        if not self.api_key:
            raise ValueError("API key not loaded")

        params = {
            "serviceKey": self.api_key,
            "keyword": keyword,
            "page": page,
            "perPage": per_page,
            "type": "json",
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def get_policy_detail(self, policy_id: str) -> Dict:
        """정책 상세 정보 조회"""
        if not self.api_key:
            raise ValueError("API key not loaded")

        params = {"serviceKey": self.api_key, "policyId": policy_id, "type": "json"}

        try:
            response = requests.get(f"{self.base_url}/detail", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Policy detail request failed: {e}")
            raise


# 싱글톤 인스턴스
_client = None


def get_data_client() -> DataGoKrClient:
    """데이터 클라이언트 싱글톤 반환"""
    global _client
    if _client is None:
        _client = DataGoKrClient()
    return _client
