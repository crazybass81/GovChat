"""
정책 캐싱 전략 구현
"""

import hashlib
import json
import time
from typing import Dict, Optional


class PolicyCache:
    """정책 매칭 결과 캐싱"""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict] = {}

    def _generate_key(self, user_profile: Dict, policy_id: str) -> str:
        """캐시 키 생성 - 파티션 키 쏠림 방지"""
        # 사용자 ID가 있으면 우선 사용 (파티션 분산)
        user_id = user_profile.get("user_id", "")
        if not user_id:
            # 프로필 해시로 대체
            profile_str = json.dumps(user_profile, sort_keys=True)
            user_id = hashlib.sha256(profile_str.encode()).hexdigest()[:8]

        # 시간 기반 prefix로 핫 파티션 방지
        time_prefix = str(int(time.time() // 3600))  # 시간별 분산
        key_data = f"{time_prefix}:{user_id}:{policy_id}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, user_profile: Dict, policy_id: str) -> Optional[Dict]:
        """캐시에서 매칭 결과 조회"""
        key = self._generate_key(user_profile, policy_id)

        if key not in self.cache:
            return None

        cached_data = self.cache[key]

        # TTL 확인
        if time.time() - cached_data["timestamp"] > self.ttl_seconds:
            del self.cache[key]
            return None

        return cached_data["result"]

    def set(self, user_profile: Dict, policy_id: str, result: Dict):
        """매칭 결과 캐싱"""
        key = self._generate_key(user_profile, policy_id)

        self.cache[key] = {"result": result, "timestamp": time.time()}

    def clear_expired(self):
        """만료된 캐시 정리"""
        current_time = time.time()
        expired_keys = [
            key
            for key, data in self.cache.items()
            if current_time - data["timestamp"] > self.ttl_seconds
        ]

        for key in expired_keys:
            del self.cache[key]


class DynamoDBCache:
    """DynamoDB 기반 캐싱"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self._table = None

    @property
    def table(self):
        """DynamoDB 테이블 lazy loading"""
        if self._table is None:
            import boto3

            dynamodb = boto3.resource("dynamodb")
            self._table = dynamodb.Table(self.table_name)
        return self._table

    def get_match_score(self, user_id: str, policy_id: str) -> Optional[float]:
        """매칭 점수 조회"""
        try:
            response = self.table.get_item(
                Key={"pk": f"USER#{user_id}", "sk": f"POLICY#{policy_id}"}
            )

            if "Item" in response:
                item = response["Item"]
                current_time = int(time.time())

                # TTL 확인 (이중 만료 필드 사용)
                ttl = item.get("ttl", 0)
                expire_at = item.get("expire_at", 0)

                # TTL 지연 고려 - expire_at 우선
                if expire_at > current_time or (expire_at == 0 and ttl > current_time):
                    return item.get("match_score")

            return None
        except Exception:
            return None

    def set_match_score(self, user_id: str, policy_id: str, score: float, ttl_hours: int = 24):
        """매칭 점수 저장 - 이중 만료 필드 사용"""
        try:
            current_time = int(time.time())
            ttl = current_time + (ttl_hours * 3600)
            expire_at = current_time + (ttl_hours * 3600) - 300  # 5분 여유

            # 파티션 키 분산을 위한 prefix 추가
            time_prefix = str(current_time // 3600)

            self.table.put_item(
                Item={
                    "pk": f"{time_prefix}#USER#{user_id}",
                    "sk": f"POLICY#{policy_id}",
                    "match_score": score,
                    "ttl": ttl,
                    "expire_at": expire_at,  # 이중 만료 필드
                    "updated_at": current_time,
                    "cache_version": "1.0",
                }
            )
        except Exception:
            pass  # 캐시 저장 실패해도 메인 로직에 영향 없음


# 글로벌 캐시 인스턴스
policy_cache = PolicyCache()


# DynamoDB 캐시는 lazy loading
def get_dynamo_cache():
    import os

    return DynamoDBCache(os.environ.get("CACHE_TABLE", "govchat-cache-v3"))
