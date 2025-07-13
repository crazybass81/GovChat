"""
구조화 로깅 - JSON 형식 + CloudWatch EMF
"""

import json
import logging
import time
from typing import Any

import boto3


class StructuredLogger:
    """구조화된 JSON 로깅"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON 포맷터 설정
        handler = logging.StreamHandler()
        formatter = JsonFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # CloudWatch 클라이언트
        try:
            self.cloudwatch = boto3.client("cloudwatch", region_name="us-east-1")
        except Exception:
            self.cloudwatch = None  # 테스트 환경에서는 None

    def info(self, message: str, **kwargs):
        """정보 로그"""
        self._log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs):
        """에러 로그"""
        self._log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self._log("WARNING", message, **kwargs)

    def _log(self, level: str, message: str, **kwargs):
        """내부 로깅 메서드"""
        log_data = {
            "timestamp": int(time.time() * 1000),
            "level": level,
            "message": message,
            **kwargs,
        }

        # PII 마스킹
        log_data = self._mask_pii(log_data)

        if level == "INFO":
            self.logger.info(json.dumps(log_data, ensure_ascii=False))
        elif level == "ERROR":
            self.logger.error(json.dumps(log_data, ensure_ascii=False))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_data, ensure_ascii=False))

    def metric(self, metric_name: str, value: float, unit: str = "Count", **dimensions):
        """CloudWatch 메트릭 전송"""
        if not self.cloudwatch:
            return  # CloudWatch 클라이언트가 없으면 스킵

        try:
            self.cloudwatch.put_metric_data(
                Namespace="GovChat",
                MetricData=[
                    {
                        "MetricName": metric_name,
                        "Value": value,
                        "Unit": unit,
                        "Dimensions": [{"Name": k, "Value": str(v)} for k, v in dimensions.items()],
                    }
                ],
            )
        except Exception as e:
            self.error(f"Failed to send metric: {e}")

    def _mask_pii(self, data: dict[str, Any]) -> dict[str, Any]:
        """PII 마스킹"""
        sensitive_fields = ["email", "phone", "name", "address"]

        def mask_recursive(obj):
            if isinstance(obj, dict):
                return {
                    k: "***MASKED***" if k.lower() in sensitive_fields else mask_recursive(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [mask_recursive(item) for item in obj]
            return obj

        return mask_recursive(data)


class JsonFormatter(logging.Formatter):
    """JSON 로그 포맷터"""

    def format(self, record):
        log_data = {
            "timestamp": int(record.created * 1000),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


# 전역 로거 인스턴스
logger = StructuredLogger("govchat")
