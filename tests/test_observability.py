"""
관측성 및 모니터링 테스트
"""

import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "infra"))

from src.common.cache_strategy import PolicyCache
from src.common.monitoring import MetricCollector, create_dashboard_config
from src.common.observability import HealthChecker


def test_metric_collector():
    """메트릭 수집기 테스트"""
    collector = MetricCollector()

    collector.add_metric("TestMetric", 1.0, "Count", endpoint="test")
    assert len(collector.metrics) == 1

    metric = collector.metrics[0]
    assert metric["MetricName"] == "TestMetric"
    assert metric["Value"] == 1.0
    assert metric["Unit"] == "Count"


def test_policy_cache():
    """정책 캐싱 테스트"""
    cache = PolicyCache(ttl_seconds=1)

    user_profile = {"id": "test_user", "age": 25}
    policy_id = "policy_123"
    result = {"score": 85}

    # 캐시 저장
    cache.set(user_profile, policy_id, result)

    # 캐시 조회
    cached_result = cache.get(user_profile, policy_id)
    assert cached_result == result

    # TTL 만료 후 조회
    time.sleep(1.1)
    expired_result = cache.get(user_profile, policy_id)
    assert expired_result is None


def test_dashboard_config():
    """대시보드 설정 테스트"""
    config = create_dashboard_config()

    assert "widgets" in config
    assert len(config["widgets"]) >= 2

    # 첫 번째 위젯 확인
    first_widget = config["widgets"][0]
    assert first_widget["type"] == "metric"
    assert "properties" in first_widget


def test_health_checker():
    """헬스 체커 테스트"""
    checker = HealthChecker()

    # 성공하는 체크 추가
    def healthy_check():
        return True

    # 실패하는 체크 추가
    def unhealthy_check():
        return False

    checker.add_check("healthy_service", healthy_check)
    checker.add_check("unhealthy_service", unhealthy_check)

    results = checker.run_checks()

    assert results["overall_status"] == "unhealthy"
    assert results["checks"]["healthy_service"]["status"] == "healthy"
    assert results["checks"]["unhealthy_service"]["status"] == "unhealthy"


def test_cache_key_generation():
    """캐시 키 생성 테스트"""
    cache = PolicyCache()

    user1 = {"id": "user1", "age": 25}
    user2 = {"id": "user2", "age": 25}
    policy_id = "policy_123"

    key1 = cache._generate_key(user1, policy_id)
    key2 = cache._generate_key(user2, policy_id)
    key3 = cache._generate_key(user1, policy_id)

    # 다른 사용자는 다른 키
    assert key1 != key2

    # 같은 사용자+정책은 같은 키
    assert key1 == key3
