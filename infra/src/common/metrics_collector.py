"""
고도화된 메트릭 수집 및 EMF 전송
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

import boto3


class MetricCollector:
    """배치 전송 기반 메트릭 수집기"""

    def __init__(self, namespace: str = "GovChat", batch_size: int = 20):
        self.namespace = namespace
        self.batch_size = batch_size
        self.metrics_buffer: List[Dict] = []
        self.cloudwatch = boto3.client("cloudwatch")

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
    ):
        """메트릭을 버퍼에 추가"""
        metric_data = {
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Timestamp": datetime.utcnow(),
        }

        if dimensions:
            metric_data["Dimensions"] = [{"Name": k, "Value": v} for k, v in dimensions.items()]

        self.metrics_buffer.append(metric_data)

        # 배치 크기 도달 시 자동 전송
        if len(self.metrics_buffer) >= self.batch_size:
            self.flush()

    def put_cache_hit_rate(self, hit_count: int, total_count: int, cache_type: str = "policy"):
        """캐시 효율성 메트릭"""
        if total_count > 0:
            hit_rate = (hit_count / total_count) * 100
            self.put_metric("CacheHitRate", hit_rate, "Percent", {"CacheType": cache_type})

            # 개별 카운트도 전송
            self.put_metric("CacheHits", hit_count, "Count", {"CacheType": cache_type})
            self.put_metric(
                "CacheMisses", total_count - hit_count, "Count", {"CacheType": cache_type}
            )

    def put_lambda_performance(
        self, function_name: str, duration_ms: float, memory_used_mb: int, cold_start: bool = False
    ):
        """Lambda 성능 메트릭"""
        dimensions = {"FunctionName": function_name}

        self.put_metric("Duration", duration_ms, "Milliseconds", dimensions)
        self.put_metric("MemoryUsed", memory_used_mb, "Megabytes", dimensions)

        if cold_start:
            self.put_metric("ColdStart", 1, "Count", dimensions)

    def put_circuit_breaker_state(self, service_name: str, state: str, failure_count: int = 0):
        """Circuit Breaker 상태 메트릭"""
        dimensions = {"ServiceName": service_name}

        # 상태별 메트릭 (CLOSED=0, OPEN=1, HALF_OPEN=2)
        state_value = {"CLOSED": 0, "OPEN": 1, "HALF_OPEN": 2}.get(state, 0)
        self.put_metric("CircuitBreakerState", state_value, "None", dimensions)

        if failure_count > 0:
            self.put_metric("CircuitBreakerFailures", failure_count, "Count", dimensions)

    def flush(self):
        """버퍼의 모든 메트릭을 CloudWatch로 전송"""
        if not self.metrics_buffer:
            return

        try:
            # 배치 단위로 전송 (최대 20개씩)
            for i in range(0, len(self.metrics_buffer), 20):
                batch = self.metrics_buffer[i : i + 20]

                self.cloudwatch.put_metric_data(Namespace=self.namespace, MetricData=batch)

            self.metrics_buffer.clear()

        except Exception as e:
            # 메트릭 전송 실패해도 메인 로직에 영향 없음
            print(f"Failed to send metrics: {e}")
            self.metrics_buffer.clear()

    def __del__(self):
        """소멸자에서 남은 메트릭 전송"""
        self.flush()


class EMFLogger:
    """Embedded Metric Format 로거"""

    def __init__(self, namespace: str = "GovChat"):
        self.namespace = namespace

    def log_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
        properties: Optional[Dict] = None,
    ):
        """EMF 형식으로 메트릭 로깅"""

        emf_log = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": self.namespace,
                        "Dimensions": [list(dimensions.keys())] if dimensions else [],
                        "Metrics": [{"Name": metric_name, "Unit": unit}],
                    }
                ],
            }
        }

        # 메트릭 값 추가
        emf_log[metric_name] = value

        # 차원 추가
        if dimensions:
            emf_log.update(dimensions)

        # 추가 속성
        if properties:
            emf_log.update(properties)

        # CloudWatch Logs로 출력 (Lambda에서 자동으로 EMF 처리)
        print(json.dumps(emf_log))


# 글로벌 인스턴스
metric_collector = MetricCollector()
emf_logger = EMFLogger()


def track_cache_performance(func):
    """캐시 성능 추적 데코레이터"""

    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)

            # 캐시 히트/미스 추적
            if hasattr(result, "cache_hit"):
                if result.cache_hit:
                    metric_collector.put_metric("CacheHit", 1, "Count")
                else:
                    metric_collector.put_metric("CacheMiss", 1, "Count")

            return result

        finally:
            duration = (time.time() - start_time) * 1000
            metric_collector.put_metric(
                "CacheOperationDuration", duration, "Milliseconds", {"Operation": func.__name__}
            )

    return wrapper
