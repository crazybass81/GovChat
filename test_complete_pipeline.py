#!/usr/bin/env python3
"""
완전한 K-Startup 데이터 수집 및 처리 파이프라인 테스트
"""

import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import re

def test_complete_data_collection():
    """완전한 데이터 수집 테스트"""
    print("🚀 완전한 K-Startup 데이터 수집 파이프라인 테스트\n")
    
    # 1. API 데이터 수집
    print("📡 1단계: K-Startup API 데이터 수집...")
    policies = fetch_kstartup_data()
    print(f"   수집된 정책 수: {len(policies)}")
    
    # 2. 첫 번째 정책 상세 분석
    if policies:
        policy = policies[0]
        print(f"\n📋 2단계: 첫 번째 정책 상세 분석")
        print(f"   정책명: {policy.get('title', '')}")
        print(f"   설명: {policy.get('description', '')[:100]}...")
        print(f"   특성: {policy.get('characteristics', '')[:100]}...")
        print(f"   지원내용: {policy.get('support_content', '')[:100]}...")
        print(f"   대상정보: {policy.get('target_info', '')[:100]}...")
        print(f"   예산정보: {policy.get('budget_info', '')}")
        print(f"   상세URL: {policy.get('detail_url', '')}")
        
        # 3. 상세 페이지 크롤링 테스트
        print(f"\n🕷️ 3단계: 상세 페이지 크롤링 테스트...")
        if policy.get('detail_url'):
            detail_info = crawl_detail_page(policy['detail_url'])
            if detail_info:
                print("   크롤링 성공!")
                for key, value in detail_info.items():
                    if value and key != 'full_text':
                        print(f"   {key}: {value[:100]}...")
            else:
                print("   크롤링 실패 또는 정보 없음")
        
        # 4. 임베딩 텍스트 생성 테스트
        print(f"\n🧠 4단계: 임베딩용 텍스트 생성...")
        embedding_text = generate_embedding_text(policy)
        print(f"   텍스트 길이: {len(embedding_text)} 문자")
        print(f"   텍스트 미리보기: {embedding_text[:200]}...")
        
        # 5. 데이터 구조 완성도 체크
        print(f"\n✅ 5단계: 데이터 구조 완성도 체크")
        check_data_completeness(policy)

def fetch_kstartup_data():
    """K-Startup API 데이터 수집"""
    try:
        url = "https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/getBusinessInformation"
        params = {
            'serviceKey': '0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA==',
            'numOfRows': 5,  # 테스트용 5개만
            'pageNo': 1
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            return parse_kstartup_xml(response.text)
        else:
            print(f"   API 호출 실패: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"   API 오류: {e}")
        return []

def parse_kstartup_xml(xml_data):
    """XML 파싱"""
    try:
        root = ET.fromstring(xml_data)
        items = root.findall('.//item')
        policies = []
        
        for item in items:
            cols = {col.get('name'): col.text for col in item.findall('col')}
            
            policy = {
                'policy_id': f"kstartup_{cols.get('id', '')}",
                'title': cols.get('supt_biz_titl_nm', ''),
                'description': cols.get('supt_biz_intrd_info', ''),
                'characteristics': cols.get('supt_biz_chrct', ''),
                'support_content': cols.get('biz_supt_ctnt', ''),
                'target_info': cols.get('biz_supt_trgt_info', ''),
                'budget_info': cols.get('biz_supt_bdgt_info', ''),
                'category_code': cols.get('biz_category_cd', ''),
                'detail_url': cols.get('detl_pg_url', ''),
                'biz_year': cols.get('biz_yr', '2025'),
                'agency': 'K-Startup',
                'target_age': extract_age_info(cols.get('biz_supt_trgt_info', '')),
                'support_amount': extract_budget_amount(cols.get('biz_supt_bdgt_info', '')),
                'region': extract_region_info(cols.get('biz_supt_trgt_info', '')),
                'source': 'kstartup_api'
            }
            
            if policy['title']:
                policies.append(policy)
        
        return policies
        
    except Exception as e:
        print(f"   XML 파싱 오류: {e}")
        return []

def extract_age_info(content):
    """나이 정보 추출"""
    if not content:
        return '전 연령'
    
    age_patterns = [
        r'(\d+)세\s*이하',
        r'(\d+)세\s*미만',
        r'청년.*?(\d+)세',
        r'만\s*(\d+)세'
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, content)
        if match:
            return f"{match.group(1)}세 이하"
    
    if '청년' in content:
        return '39세 이하'
    
    return '전 연령'

def extract_budget_amount(budget_info):
    """예산 정보 추출"""
    if not budget_info:
        return ''
    
    amount_patterns = [
        r'(\d+(?:\.\d+)?억원)',
        r'(\d+백만원)',
        r'(\d+조원)',
        r'최대\s*(\d+(?:\.\d+)?억원)',
        r'최대\s*(\d+백만원)'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, budget_info)
        if match:
            return match.group(1)
    
    return budget_info[:50] if budget_info else ''

def extract_region_info(target_info):
    """지역 정보 추출"""
    if not target_info:
        return '전국'
    
    regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', 
               '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
    
    for region in regions:
        if region in target_info:
            return region
    
    return '전국'

def crawl_detail_page(detail_url):
    """상세 페이지 크롤링"""
    try:
        if not detail_url.startswith('http'):
            detail_url = f"https://{detail_url}"
        
        response = requests.get(detail_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            # 간단한 텍스트 추출 (BeautifulSoup 없이)
            html_text = response.text
            
            detail_info = {
                'application_method': extract_html_section(html_text, ['신청방법', '신청절차']),
                'application_period': extract_html_section(html_text, ['신청기간', '접수기간']),
                'contact_info': extract_html_section(html_text, ['문의처', '연락처', '담당자']),
                'full_text_length': len(html_text)
            }
            
            return detail_info
            
    except Exception as e:
        print(f"   크롤링 오류: {e}")
        return {}
    
    return {}

def extract_html_section(html_text, keywords):
    """HTML에서 키워드 기반 섹션 추출"""
    for keyword in keywords:
        if keyword in html_text:
            # 키워드 주변 텍스트 추출 (간단한 방식)
            start = html_text.find(keyword)
            if start != -1:
                section = html_text[start:start+200]
                # HTML 태그 제거
                import re
                clean_text = re.sub(r'<[^>]+>', '', section)
                return clean_text.strip()
    return ''

def generate_embedding_text(policy):
    """임베딩용 텍스트 생성"""
    text_parts = [
        policy.get('title', ''),
        policy.get('description', ''),
        policy.get('characteristics', ''),
        policy.get('support_content', ''),
        policy.get('target_info', ''),
        policy.get('budget_info', ''),
        policy.get('application_method', ''),
        policy.get('contact_info', '')
    ]
    
    full_text = ' '.join([part for part in text_parts if part and part.strip()])
    
    if len(full_text) > 8000:
        full_text = full_text[:8000]
    
    return full_text

def check_data_completeness(policy):
    """데이터 완성도 체크"""
    required_fields = ['title', 'description', 'characteristics', 'support_content', 
                      'target_info', 'budget_info', 'detail_url']
    
    completed = 0
    total = len(required_fields)
    
    for field in required_fields:
        if policy.get(field) and policy[field].strip():
            completed += 1
            print(f"   ✅ {field}: 완료")
        else:
            print(f"   ❌ {field}: 누락")
    
    print(f"\n   📊 완성도: {completed}/{total} ({completed/total*100:.1f}%)")

if __name__ == "__main__":
    test_complete_data_collection()