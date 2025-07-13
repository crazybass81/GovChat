"""
부하 테스트 및 성능 벤치마크
"""

import asyncio
import json
import random
import statistics
import time

import aiohttp


class LoadTester:
    """API 부하 테스트 클래스"""

    def __init__(self, base_url: str, max_workers: int = 50):
        self.base_url = base_url.rstrip("/")
        self.max_workers = max_workers
        self.results = []

    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, payload: dict):
        """단일 HTTP 요청 실행"""
        start_time = time.time()

        try:
            async with session.post(f"{self.base_url}{endpoint}", json=payload) as response:
                response_time = (time.time() - start_time) * 1000  # ms
                status = response.status

                if status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "response_time": response_time,
                        "status": status,
                        "endpoint": endpoint,
                        "data_size": len(json.dumps(data)),
                    }
                else:
                    return {
                        "success": False,
                        "response_time": response_time,
                        "status": status,
                        "endpoint": endpoint,
                        "error": f"HTTP {status}",
                    }

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return {
                "success": False,
                "response_time": response_time,
                "status": 0,
                "endpoint": endpoint,
                "error": str(e),
            }

    async def run_concurrent_requests(self, endpoint: str, payload: dict, num_requests: int):
        """동시 요청 실행"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [self.make_request(session, endpoint, payload) for _ in range(num_requests)]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 예외 처리
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append(
                        {
                            "success": False,
                            "response_time": 30000,  # 타임아웃
                            "status": 0,
                            "endpoint": endpoint,
                            "error": str(result),
                        }
                    )
                else:
                    processed_results.append(result)

            return processed_results

    def generate_test_payloads(self):
        """테스트용 페이로드 생성"""
        payloads = {
            "/chat": [{"message": "안녕하세요", "session_id": f"test_{i}"} for i in range(10)],
            "/search": [{"query": f"창업 지원 {i}", "limit": 10} for i in range(10)],
            "/match": [
                {
                    "user_profile": {
                        "age": random.randint(20, 60),
                        "region": random.choice(["서울", "경기", "부산"]),
                        "business_type": random.choice(["개인사업자", "법인"]),
                    },
                    "policy_id": f"policy_{i}",
                }
                for i in range(10)
            ],
            "/extract": [
                {"policy_text": f"만 {random.randint(20, 40)}세 이하 창업자 지원 {i}"}
                for i in range(10)
            ],
        }
        return payloads

    async def run_load_test(self, rps_target: int = 100, duration_seconds: int = 60):
        """부하 테스트 실행"""
        print(f"부하 테스트 시작: {rps_target} RPS, {duration_seconds}초 동안")

        payloads = self.generate_test_payloads()
        endpoints = list(payloads.keys())

        start_time = time.time()
        all_results = []

        # RPS 제어를 위한 간격 계산
        request_interval = 1.0 / rps_target

        while time.time() - start_time < duration_seconds:
            batch_start = time.time()

            # 랜덤 엔드포인트 선택
            endpoint = random.choice(endpoints)
            payload = random.choice(payloads[endpoint])

            # 단일 요청 실행
            connector = aiohttp.TCPConnector(limit=10)
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                result = await self.make_request(session, endpoint, payload)
                all_results.append(result)

            # RPS 제어를 위한 대기
            elapsed = time.time() - batch_start
            if elapsed < request_interval:
                await asyncio.sleep(request_interval - elapsed)

        self.results = all_results
        return self.analyze_results()

    def analyze_results(self):
        """결과 분석"""
        if not self.results:
            return {"error": "No results to analyze"}

        # 성공/실패 분리
        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]

        # 응답시간 통계
        response_times = [r["response_time"] for r in successful]

        if response_times:
            response_stats = {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": self._percentile(response_times, 95),
                "p99": self._percentile(response_times, 99),
            }
        else:
            response_stats = {}

        # 엔드포인트별 통계
        endpoint_stats = {}
        for endpoint in set(r["endpoint"] for r in self.results):
            endpoint_results = [r for r in self.results if r["endpoint"] == endpoint]
            endpoint_successful = [r for r in endpoint_results if r["success"]]

            endpoint_stats[endpoint] = {
                "total_requests": len(endpoint_results),
                "successful_requests": len(endpoint_successful),
                "success_rate": len(endpoint_successful) / len(endpoint_results) * 100,
                "avg_response_time": statistics.mean(
                    [r["response_time"] for r in endpoint_successful]
                )
                if endpoint_successful
                else 0,
            }

        # 에러 분석
        error_types = {}
        for result in failed:
            error = result.get("error", "Unknown")
            error_types[error] = error_types.get(error, 0) + 1

        return {
            "summary": {
                "total_requests": len(self.results),
                "successful_requests": len(successful),
                "failed_requests": len(failed),
                "success_rate": len(successful) / len(self.results) * 100,
                "total_duration": max(r.get("timestamp", 0) for r in self.results)
                - min(r.get("timestamp", 0) for r in self.results)
                if self.results
                else 0,
            },
            "response_time_stats": response_stats,
            "endpoint_stats": endpoint_stats,
            "error_analysis": error_types,
        }

    def _percentile(self, data, percentile):
        """백분위수 계산"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class StressTester:
    """스트레스 테스트 - 시스템 한계 측정"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.load_tester = LoadTester(base_url)

    async def find_breaking_point(self, start_rps: int = 10, max_rps: int = 1000, step: int = 10):
        """시스템 한계점 찾기"""
        print("스트레스 테스트 시작 - 시스템 한계점 탐색")

        results = []
        current_rps = start_rps

        while current_rps <= max_rps:
            print(f"테스트 중: {current_rps} RPS")

            # 30초간 테스트
            result = await self.load_tester.run_load_test(current_rps, 30)

            success_rate = result["summary"]["success_rate"]
            p95_latency = result["response_time_stats"].get("p95", 0)

            results.append(
                {
                    "rps": current_rps,
                    "success_rate": success_rate,
                    "p95_latency": p95_latency,
                    "breaking_point": success_rate < 95 or p95_latency > 1200,  # SLA 위반
                }
            )

            print(f"결과: 성공률 {success_rate:.1f}%, P95 지연시간 {p95_latency:.0f}ms")

            # 한계점 도달 시 중단
            if success_rate < 95 or p95_latency > 1200:
                print(f"한계점 도달: {current_rps} RPS")
                break

            current_rps += step

            # 시스템 복구 대기
            await asyncio.sleep(10)

        return results


async def run_performance_benchmark():
    """성능 벤치마크 실행"""
    # 실제 API 엔드포인트로 변경 필요
    base_url = "https://your-api-gateway-url.amazonaws.com/prod"

    load_tester = LoadTester(base_url)

    print("=== 성능 벤치마크 시작 ===")

    # 1. 기본 부하 테스트 (100 RPS, 60초)
    print("\n1. 기본 부하 테스트")
    result = await load_tester.run_load_test(rps_target=100, duration_seconds=60)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 2. 동시성 테스트 (1000개 동시 요청)
    print("\n2. 동시성 테스트")
    concurrent_results = await load_tester.run_concurrent_requests(
        "/chat", {"message": "동시성 테스트", "session_id": "concurrent_test"}, 1000
    )

    success_count = sum(1 for r in concurrent_results if r["success"])
    avg_response_time = statistics.mean(
        [r["response_time"] for r in concurrent_results if r["success"]]
    )

    print(f"동시 요청 1000개 중 {success_count}개 성공")
    print(f"평균 응답시간: {avg_response_time:.2f}ms")

    # 3. 스트레스 테스트
    print("\n3. 스트레스 테스트")
    stress_tester = StressTester(base_url)
    stress_results = await stress_tester.find_breaking_point(start_rps=50, max_rps=500, step=25)

    print("스트레스 테스트 결과:")
    for result in stress_results:
        status = "❌ 한계점" if result["breaking_point"] else "✅ 정상"
        print(
            f"{result['rps']} RPS: 성공률 {result['success_rate']:.1f}%, P95 {result['p95_latency']:.0f}ms {status}"
        )


if __name__ == "__main__":
    # 테스트 실행
    asyncio.run(run_performance_benchmark())
