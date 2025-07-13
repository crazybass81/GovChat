"""
관측성 및 알람 설정
"""

import os
import time
from typing import Dict, List


def create_cloudwatch_alarms() -> List[Dict]:
    """CloudWatch 알람 설정"""
    return [
        {
            "AlarmName": "GovChat-HighErrorRate",
            "ComparisonOperator": "GreaterThanThreshold",
            "EvaluationPeriods": 2,
            "MetricName": "RequestError",
            "Namespace": "GovChat",
            "Period": 300,
            "Statistic": "Sum",
            "Threshold": 10.0,
            "ActionsEnabled": True,
            "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:govchat-alerts"],
            "AlarmDescription": "High error rate detected",
            "Unit": "Count",
        },
        {
            "AlarmName": "GovChat-CircuitBreakerOpen",
            "ComparisonOperator": "GreaterThanThreshold",
            "EvaluationPeriods": 1,
            "MetricName": "CircuitBreakerOpen",
            "Namespace": "GovChat",
            "Period": 60,
            "Statistic": "Sum",
            "Threshold": 0.0,
            "ActionsEnabled": True,
            "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:govchat-alerts"],
            "AlarmDescription": "Circuit breaker opened - service degraded",
            "Unit": "Count",
        },
        {
            "AlarmName": "GovChat-HighLatency",
            "ComparisonOperator": "GreaterThanThreshold",
            "EvaluationPeriods": 3,
            "MetricName": "ProcessingTime",
            "Namespace": "GovChat",
            "Period": 300,
            "Statistic": "Average",
            "Threshold": 2000.0,
            "ActionsEnabled": True,
            "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:govchat-alerts"],
            "AlarmDescription": "High processing latency detected",
            "Unit": "Milliseconds",
        },
    ]


def create_log_insights_queries() -> Dict[str, str]:
    """CloudWatch Logs Insights 쿼리"""
    return {
        "error_analysis": """
            fields @timestamp, @message, error, endpoint
            | filter @message like /ERROR/
            | stats count() by endpoint
            | sort count desc
        """,
        "performance_analysis": """
            fields @timestamp, endpoint, processing_time
            | filter ispresent(processing_time)
            | stats avg(processing_time), max(processing_time), min(processing_time) by endpoint
        """,
        "rate_limit_analysis": """
            fields @timestamp, @message, source_ip, endpoint
            | filter @message like /Rate limit exceeded/
            | stats count() by source_ip, endpoint
            | sort count desc
        """,
    }


class HealthChecker:
    """서비스 헬스 체크"""

    def __init__(self):
        self.checks = []

    def add_check(self, name: str, check_func):
        """헬스 체크 추가"""
        self.checks.append((name, check_func))

    def run_checks(self) -> Dict:
        """모든 헬스 체크 실행"""
        results = {}
        overall_healthy = True

        for name, check_func in self.checks:
            try:
                result = check_func()
                results[name] = {"status": "healthy" if result else "unhealthy", "details": result}
                if not result:
                    overall_healthy = False
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
                overall_healthy = False

        return {
            "overall_status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": int(time.time()),
        }


def check_opensearch_health() -> bool:
    """OpenSearch 헬스 체크"""
    try:
        import requests

        # OpenSearch 엔드포인트 상태 확인
        endpoint = os.environ.get("OPENSEARCH_HOST")
        if not endpoint:
            return False

        response = requests.get(f"https://{endpoint}/_cluster/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def check_dynamodb_health() -> bool:
    """DynamoDB 헬스 체크"""
    try:
        import boto3

        dynamodb = boto3.client("dynamodb")
        table_name = os.environ.get("CACHE_TABLE")

        response = dynamodb.describe_table(TableName=table_name)
        return response["Table"]["TableStatus"] == "ACTIVE"
    except Exception:
        return False
