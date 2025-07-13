"""
Rate Limiting 구현
"""

import time
from typing import Dict


class RateLimiter:
    """토큰 버킷 기반 Rate Limiter"""

    def __init__(self, rate_limit: int = 50, burst_limit: int = 100):
        self.rate_limit = rate_limit  # 초당 요청 수
        self.burst_limit = burst_limit  # 버스트 허용량
        self.tokens = burst_limit
        self.last_refill = time.time()

    def allow_request(self) -> bool:
        """요청 허용 여부 확인"""
        now = time.time()

        # 토큰 리필
        elapsed = now - self.last_refill
        self.tokens = min(self.burst_limit, self.tokens + elapsed * self.rate_limit)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


# 글로벌 Rate Limiter 인스턴스
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(endpoint: str) -> RateLimiter:
    """엔드포인트별 Rate Limiter 반환"""
    if endpoint not in _rate_limiters:
        # 엔드포인트별 다른 제한
        limits = {
            "chat": RateLimiter(rate_limit=10, burst_limit=20),
            "search": RateLimiter(rate_limit=50, burst_limit=100),
            "question": RateLimiter(rate_limit=30, burst_limit=60),
            "match": RateLimiter(rate_limit=20, burst_limit=40),
            "extract": RateLimiter(rate_limit=15, burst_limit=30),
        }
        _rate_limiters[endpoint] = limits.get(endpoint, RateLimiter())

    return _rate_limiters[endpoint]
