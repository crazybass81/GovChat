#!/usr/bin/env python3
"""
시스템 헬스체크 스크립트
"""

import time

import requests

API_BASE = "https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod"


def health_check():
    """전체 시스템 헬스체크"""
    endpoints = [
        ("/question", {"userProfile": {"region": "서울"}, "policyText": "만 39세 이하"}),
        ("/search", {"q": "청년 지원"}),
        ("/extract", {"policyText": "만 39세 이하 서울 청년"}),
        ("/match", {"userProfile": {"age": 30}, "policyText": "만 39세 이하"}),
    ]

    results = {}

    for endpoint, payload in endpoints:
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE}{endpoint}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response_time = time.time() - start_time

            results[endpoint] = {
                "status": "OK" if response.status_code == 200 else "FAIL",
                "status_code": response.status_code,
                "response_time": f"{response_time:.2f}s",
                "response_size": len(response.text),
            }

        except Exception as e:
            results[endpoint] = {"status": "ERROR", "error": str(e)}

    # 결과 출력
    print("=== Health Check Results ===")
    for endpoint, result in results.items():
        print(f"{endpoint}: {result['status']}")
        if result["status"] == "OK":
            print(f"  Response Time: {result['response_time']}")
        elif result["status"] == "ERROR":
            print(f"  Error: {result['error']}")

    return results


if __name__ == "__main__":
    health_check()
