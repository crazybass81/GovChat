"""
모니터링 및 대시보드 구성
"""

from typing import Dict


class MetricCollector:
    """CloudWatch 메트릭 수집기"""

    def __init__(self):
        self.metrics = []

    def add_metric(self, name: str, value: float, unit: str = "Count", **dimensions):
        """메트릭 추가"""
        metric = {
            "MetricName": name,
            "Value": value,
            "Unit": unit,
            "Dimensions": [{"Name": k, "Value": str(v)} for k, v in dimensions.items()],
        }
        self.metrics.append(metric)

    def flush_metrics(self):
        """메트릭 전송"""
        if not self.metrics:
            return

        try:
            import boto3

            cloudwatch = boto3.client("cloudwatch")

            # 배치로 메트릭 전송
            cloudwatch.put_metric_data(Namespace="GovChat", MetricData=self.metrics)
            self.metrics.clear()
        except Exception:
            pass  # 메트릭 전송 실패해도 메인 로직에 영향 없음


def create_dashboard_config() -> Dict:
    """CloudWatch 대시보드 설정"""
    return {
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["GovChat", "RequestSuccess", "endpoint", "chat"],
                        [".", "RequestError", ".", "."],
                        [".", "RateLimitExceeded", ".", "."],
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Chat Endpoint Metrics",
                },
            },
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["GovChat", "CircuitBreakerOpen", "component", "circuit_breaker"],
                        [".", "CircuitBreakerHalfOpen", ".", "."],
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "Circuit Breaker Status",
                },
            },
        ]
    }


# 글로벌 메트릭 수집기
metric_collector = MetricCollector()
