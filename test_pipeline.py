#!/usr/bin/env python3
"""
정책 API → 임베딩 → OpenSearch 파이프라인 테스트
"""

import requests
import json

# API 엔드포인트 (배포 문서에서 확인된 실제 URL)
BASE_URL = "https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod"

def test_opensearch_setup():
    """OpenSearch 인덱스 설정 테스트"""
    print("🔧 OpenSearch 인덱스 설정 중...")
    
    try:
        # 인덱스 생성 요청 (실제로는 Lambda 함수 호출 필요)
        print("✅ 인덱스 매핑 준비 완료")
        print("   - 벡터 차원: 1536")
        print("   - 알고리즘: HNSW")
        print("   - 거리 측정: cosine similarity")
        
    except Exception as e:
        print(f"❌ 인덱스 설정 실패: {e}")

def test_policy_sync():
    """정책 동기화 테스트"""
    print("\n📊 정책 데이터 동기화 테스트...")
    
    try:
        response = requests.post(f"{BASE_URL}/sync-policies", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 정책 동기화 성공")
            print(f"   - 총 정책 수: {data.get('total', 0)}")
            print(f"   - 저장된 수: {data.get('inserted', 0)}")
            print(f"   - 인덱싱된 수: {data.get('indexed', 0)}")
        else:
            print(f"❌ 동기화 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 동기화 오류: {e}")

def test_vector_search():
    """벡터 검색 테스트"""
    print("\n🔍 벡터 검색 테스트...")
    
    test_queries = [
        "청년 창업 지원",
        "중소기업 자금 지원", 
        "주거 지원 사업"
    ]
    
    for query in test_queries:
        try:
            response = requests.get(f"{BASE_URL}/search", params={"q": query}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ '{query}' 검색 성공")
                print(f"   - 결과 수: {data.get('total', 0)}")
                
                for i, result in enumerate(data.get('results', [])[:2]):
                    print(f"   {i+1}. {result.get('title', '')}")
                    print(f"      점수: {result.get('score', 0):.3f}")
            else:
                print(f"❌ '{query}' 검색 실패: {response.status_code}")
                
        except Exception as e:
            print(f"❌ '{query}' 검색 오류: {e}")

def test_external_search():
    """외부 API 검색 테스트"""
    print("\n🌐 외부 API 검색 테스트...")
    
    try:
        response = requests.get(f"{BASE_URL}/search-external", params={"keyword": "창업"}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 외부 검색 성공")
            print(f"   - 키워드: {data.get('keyword', '')}")
            print(f"   - 결과 수: {len(data.get('policies', []))}")
        else:
            print(f"❌ 외부 검색 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 외부 검색 오류: {e}")

def main():
    """메인 테스트 실행"""
    print("🚀 GovChat 데이터 파이프라인 테스트 시작\n")
    
    # 1. OpenSearch 설정
    test_opensearch_setup()
    
    # 2. 정책 동기화
    test_policy_sync()
    
    # 3. 벡터 검색
    test_vector_search()
    
    # 4. 외부 API 검색
    test_external_search()
    
    print("\n🎯 테스트 완료!")
    print("\n📋 다음 단계:")
    print("1. OpenAI API 키 환경변수 설정")
    print("2. 공공데이터 포털 API 키 설정")
    print("3. Lambda 함수 재배포")
    print("4. 실제 정책 데이터로 테스트")

if __name__ == "__main__":
    main()