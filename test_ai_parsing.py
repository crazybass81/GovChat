#!/usr/bin/env python3
"""
AI 기반 동적 API 파싱 테스트
"""

import requests
import json

def test_ai_parsing():
    """AI 파싱 시스템 테스트"""
    print("🤖 AI 기반 동적 API 파싱 테스트 시작...")
    
    # K-Startup API 실제 데이터 가져오기
    print("\n📡 K-Startup API 데이터 수집 중...")
    
    try:
        url = "https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/getBusinessInformation"
        params = {
            'serviceKey': '0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA==',
            'numOfRows': 5,  # 테스트용 5개만
            'pageNo': 1
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ API 호출 성공: {len(response.text)} bytes")
            
            # 실제 필드들 분석
            analyze_actual_fields(response.text)
            
            # AI 파싱 시뮬레이션 (OpenAI API 키 없이)
            simulate_ai_parsing(response.text)
            
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")

def analyze_actual_fields(xml_data):
    """실제 XML 필드 분석"""
    print("\n🔍 실제 XML 필드 분석...")
    
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        
        # 모든 필드 수집
        all_fields = set()
        sample_data = {}
        
        items = root.findall('.//item')
        if items:
            first_item = items[0]
            cols = first_item.findall('col')
            
            print(f"📊 발견된 필드 수: {len(cols)}")
            print("\n📋 실제 필드 목록:")
            
            for col in cols:
                field_name = col.get('name')
                field_value = col.text or ''
                all_fields.add(field_name)
                sample_data[field_name] = field_value[:100] + '...' if len(field_value) > 100 else field_value
                
                print(f"   • {field_name}: {field_value[:50]}{'...' if len(field_value) > 50 else ''}")
        
        print(f"\n✅ 총 {len(all_fields)}개 필드 발견")
        
        # 중요 필드 식별
        important_fields = identify_important_fields(all_fields)
        print(f"\n🎯 중요 필드들: {important_fields}")
        
    except Exception as e:
        print(f"❌ 필드 분석 오류: {e}")

def identify_important_fields(fields):
    """중요 필드 자동 식별"""
    important_patterns = {
        'title': ['titl', 'name', 'nm'],
        'description': ['intrd', 'cont', 'desc'],
        'budget': ['bdgt', 'budget', 'amount'],
        'target': ['trgt', 'target'],
        'support': ['supt', 'support'],
        'url': ['url', 'link'],
        'period': ['period', 'date'],
        'agency': ['inst', 'agency', 'org']
    }
    
    identified = {}
    for category, patterns in important_patterns.items():
        for field in fields:
            field_lower = field.lower()
            if any(pattern in field_lower for pattern in patterns):
                if category not in identified:
                    identified[category] = []
                identified[category].append(field)
    
    return identified

def simulate_ai_parsing(xml_data):
    """AI 파싱 시뮬레이션"""
    print("\n🤖 AI 파싱 시뮬레이션...")
    
    # GPT 프롬프트 생성 (실제로는 OpenAI API 호출)
    prompt = f"""
다음은 정부 지원사업 API 응답 데이터입니다. 이 데이터에서 정책 정보를 추출해서 JSON 배열로 변환해주세요.

원본 데이터 (처음 1000자):
{xml_data[:1000]}

추출해야 할 정보:
- policy_id: 정책 고유 ID
- title: 사업명/정책명  
- description: 사업 설명/소개
- agency: 주관기관
- target_info: 지원 대상
- support_content: 지원 내용
- budget_info: 예산/지원 규모
- application_period: 신청 기간
- detail_url: 상세 페이지 URL
- 기타 모든 유용한 필드들

JSON 형식으로만 응답해주세요:
[{{"policy_id": "...", "title": "...", ...}}]
"""
    
    print("📝 생성된 AI 프롬프트:")
    print(f"   길이: {len(prompt)} 문자")
    print(f"   포함된 데이터: {len(xml_data)} bytes")
    
    # 실제 AI 파싱 결과 시뮬레이션
    print("\n🎯 예상 AI 파싱 결과:")
    print("   • 5개 정책 추출 예상")
    print("   • 각 정책당 15-20개 필드 구조화")
    print("   • 상세 URL 크롤링으로 추가 정보 수집")
    print("   • 모든 정보를 포함한 1536차원 임베딩 생성")

def main():
    """메인 테스트 실행"""
    test_ai_parsing()
    
    print("\n🎉 AI 파싱 시스템 특징:")
    print("✅ 모든 API 스키마 자동 적응")
    print("✅ 필드명이 달라도 의미 기반 매핑")
    print("✅ 상세 페이지 자동 크롤링")
    print("✅ 구조화되지 않은 텍스트도 파싱")
    print("✅ 새로운 API 추가시 코드 수정 불필요")
    
    print("\n📋 다음 단계:")
    print("1. OpenAI API 키 설정")
    print("2. Lambda 함수 재배포")
    print("3. 실제 AI 파싱 테스트")
    print("4. 다른 정부 API들도 자동 연동")

if __name__ == "__main__":
    main()