#!/usr/bin/env python3
"""
K-Startup API 테스트 스크립트
"""

import requests
import json

def test_kstartup_api():
    """K-Startup API 다양한 방식으로 테스트"""
    
    # 방법 1: 전체 URL
    print("🔍 K-Startup API 테스트 시작...")
    
    urls_to_test = [
        "https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/getBusinessInformation/0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA==",
        "https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/getBusinessInformation?serviceKey=0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA==",
        "https://nidapi.k-startup.go.kr/api/kisedKstartupService/getBusinessInformation?serviceKey=0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA==",
        "https://api.k-startup.go.kr/api/kisedKstartupService/v1/getBusinessInformation?serviceKey=0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA=="
    ]
    
    for i, url in enumerate(urls_to_test, 1):
        print(f"\n📡 테스트 {i}: {url[:80]}...")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"   상태 코드: {response.status_code}")
            print(f"   응답 길이: {len(response.text)}")
            print(f"   응답 내용: {response.text[:200]}...")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   JSON 파싱 성공: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   키들: {list(data.keys())}")
                except:
                    print("   JSON 파싱 실패")
                    
        except Exception as e:
            print(f"   오류: {e}")
    
    # 방법 2: 다른 엔드포인트 시도
    print(f"\n🔍 다른 K-Startup 엔드포인트 테스트...")
    
    other_endpoints = [
        "https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/getBizInfo",
        "https://nidapi.k-startup.go.kr/api/kisedKstartupService/getBizInfo",
        "https://api.k-startup.go.kr/openapi/service/rest/getBizInfo"
    ]
    
    service_key = "0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA=="
    
    for endpoint in other_endpoints:
        print(f"\n📡 테스트: {endpoint}")
        try:
            response = requests.get(f"{endpoint}?serviceKey={service_key}", timeout=10)
            print(f"   상태: {response.status_code}")
            print(f"   응답: {response.text[:100]}...")
        except Exception as e:
            print(f"   오류: {e}")

if __name__ == "__main__":
    test_kstartup_api()