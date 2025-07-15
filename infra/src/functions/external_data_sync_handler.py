"""
외부 공공데이터 API 연동 핸들러 - 간단한 버전
"""

import json
import boto3
import os
from aws_lambda_powertools import Logger
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

try:
    import requests
except ImportError:
    requests = None

logger = Logger()

def handler(event, context):
    """외부 데이터 동기화 핸들러"""
    try:
        method = event.get("httpMethod")
        path = event.get("resource")
        
        if method == "POST" and "sync-policies" in path:
            return sync_policies()
        elif method == "GET" and "search-external" in path:
            keyword = event.get("queryStringParameters", {}).get("keyword", "")
            return search_external(keyword)
        else:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Not found"})
            }
            
    except Exception as e:
        logger.error(f"External sync error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }

def save_single_policy_to_s3(policy_data: dict, timestamp: str) -> str:
    """개별 사업의 모든 정보를 S3에 저장"""
    try:
        s3_client = boto3.client('s3')
        bucket_name = os.environ.get('DATA_BUCKET', 'govchat-data-v3-036284794745')
        
        policy_id = policy_data.get('policy_id', f'policy_{timestamp}')
        
        # S3 키 구조: policies/YYYY/MM/DD/policy_id/
        date_path = datetime.utcnow().strftime('%Y/%m/%d')
        base_key = f"policies/{date_path}/{policy_id}"
        
        saved_files = []
        
        # 1. 기본 정책 정보 저장
        basic_info = {
            'policy_id': policy_data.get('policy_id'),
            'title': policy_data.get('title'),
            'description': policy_data.get('description'),
            'agency': policy_data.get('agency'),
            'collected_at': timestamp,
            'source': policy_data.get('source')
        }
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=f"{base_key}/basic_info.json",
            Body=json.dumps(basic_info, ensure_ascii=False, indent=2),
            ContentType='application/json'
        )
        saved_files.append(f"{base_key}/basic_info.json")
        
        # 2. 원본 API 응답 데이터 저장
        if policy_data.get('raw_api_data'):
            s3_client.put_object(
                Bucket=bucket_name,
                Key=f"{base_key}/raw_api_response.xml",
                Body=policy_data['raw_api_data'],
                ContentType='application/xml'
            )
            saved_files.append(f"{base_key}/raw_api_response.xml")
        
        # 3. 상세 페이지 HTML 저장
        if policy_data.get('detail_page_html'):
            s3_client.put_object(
                Bucket=bucket_name,
                Key=f"{base_key}/detail_page.html",
                Body=policy_data['detail_page_html'],
                ContentType='text/html'
            )
            saved_files.append(f"{base_key}/detail_page.html")
        
        # 4. AI 분석 결과 저장
        if policy_data.get('ai_analysis'):
            s3_client.put_object(
                Bucket=bucket_name,
                Key=f"{base_key}/ai_analysis.json",
                Body=json.dumps(policy_data['ai_analysis'], ensure_ascii=False, indent=2),
                ContentType='application/json'
            )
            saved_files.append(f"{base_key}/ai_analysis.json")
        
        # 5. 추출된 조건들 저장
        if policy_data.get('extracted_conditions'):
            s3_client.put_object(
                Bucket=bucket_name,
                Key=f"{base_key}/conditions.json",
                Body=json.dumps(policy_data['extracted_conditions'], ensure_ascii=False, indent=2),
                ContentType='application/json'
            )
            saved_files.append(f"{base_key}/conditions.json")
        
        # 6. 전체 데이터 통합 저장
        complete_data = {
            'metadata': {
                'policy_id': policy_id,
                'collected_at': timestamp,
                'processing_version': '1.0',
                'files_saved': saved_files
            },
            'policy_data': policy_data
        }
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=f"{base_key}/complete_data.json",
            Body=json.dumps(complete_data, ensure_ascii=False, indent=2),
            ContentType='application/json'
        )
        saved_files.append(f"{base_key}/complete_data.json")
        
        logger.info(f"Saved {len(saved_files)} files for policy {policy_id} to S3")
        return base_key

def collect_complete_policy_data(basic_policy: dict) -> dict:
    """개별 사업의 모든 정보 수집"""
    try:
        complete_data = basic_policy.copy()
        
        # 1. 상세 페이지 크롤링
        if basic_policy.get('detail_url'):
            detail_html, detail_info = crawl_detail_page_complete(basic_policy['detail_url'])
            complete_data['detail_page_html'] = detail_html
            complete_data.update(detail_info)
        
        # 2. AI로 모든 데이터 분석
        ai_analysis = analyze_policy_with_ai(complete_data)
        complete_data['ai_analysis'] = ai_analysis
        
        # 3. 숨겨진 조건 추출
        hidden_conditions = extract_all_conditions_with_ai(complete_data)
        complete_data['extracted_conditions'] = hidden_conditions
        
        # 4. 메타데이터 추가
        complete_data['processing_metadata'] = {
            'processed_at': datetime.utcnow().isoformat(),
            'data_completeness_score': calculate_completeness_score(complete_data),
            'total_text_length': sum(len(str(v)) for v in complete_data.values() if isinstance(v, str)),
            'fields_count': len(complete_data)
        }
        
        return complete_data
        
    except Exception as e:
        logger.error(f"Complete data collection error: {e}")
        return basic_policy

def crawl_detail_page_complete(detail_url: str) -> tuple:
    """상세 페이지 완전 크롤링 - HTML + 구조화 데이터"""
    if not requests or not detail_url:
        return '', {}
    
    try:
        if not detail_url.startswith('http'):
            detail_url = f"https://{detail_url}"
        
        response = requests.get(detail_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            html_content = response.text
            
            # BeautifulSoup로 구조화 데이터 추출
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 모든 텍스트 추출
            structured_data = {
                'page_title': soup.title.string if soup.title else '',
                'all_text': soup.get_text(),
                'tables': extract_all_tables(soup),
                'lists': extract_all_lists(soup),
                'links': extract_all_links(soup),
                'images': extract_all_images(soup),
                'meta_tags': extract_meta_tags(soup)
            }
            
            return html_content, structured_data
            
    except Exception as e:
        logger.error(f"Complete crawling error for {detail_url}: {e}")
        return '', {}
    
    return '', {}

def extract_all_tables(soup) -> list:
    """모든 테이블 데이터 추출"""
    tables = []
    for table in soup.find_all('table'):
        rows = []
        for row in table.find_all('tr'):
            cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables

def extract_all_lists(soup) -> list:
    """모든 리스트 데이터 추출"""
    lists = []
    for ul in soup.find_all(['ul', 'ol']):
        items = [li.get_text().strip() for li in ul.find_all('li')]
        if items:
            lists.append(items)
    return lists

def extract_all_links(soup) -> list:
    """모든 링크 추출"""
    links = []
    for a in soup.find_all('a', href=True):
        links.append({
            'text': a.get_text().strip(),
            'url': a['href']
        })
    return links

def extract_all_images(soup) -> list:
    """모든 이미지 정보 추출"""
    images = []
    for img in soup.find_all('img'):
        images.append({
            'src': img.get('src', ''),
            'alt': img.get('alt', ''),
            'title': img.get('title', '')
        })
    return images

def extract_meta_tags(soup) -> dict:
    """메타 태그 정보 추출"""
    meta_data = {}
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        if name and content:
            meta_data[name] = content
    return meta_data

def analyze_policy_with_ai(policy_data: dict) -> dict:
    """정책 데이터 AI 종합 분석"""
    if not requests:
        return {}
    
    try:
        # 모든 텍스트 데이터 결합
        all_text = ' '.join([
            str(policy_data.get('title', '')),
            str(policy_data.get('description', '')),
            str(policy_data.get('all_text', '')),
            str(policy_data.get('support_content', '')),
            str(policy_data.get('target_info', ''))
        ])
        
        if len(all_text) > 12000:
            all_text = all_text[:12000]
        
        prompt = f"""
다음은 정부 지원사업의 모든 정보입니다. 이를 종합적으로 분석해주세요:

{all_text}

다음 항목들을 분석해주세요:
1. 지원 대상의 모든 조건 (나이, 지역, 소득, 업종, 기업규모 등)
2. 지원 내용의 상세 분류
3. 신청 절차 및 요구사항
4. 선정 기준 및 평가 방법
5. 예산 및 지원 규모
6. 신청 기간 및 일정
7. 문의처 및 담당자
8. 숨겨진 자격 요건이나 제약 사항

JSON 형식으로 응답:
{{
  "target_conditions": {{}},
  "support_details": {{}},
  "application_process": {{}},
  "selection_criteria": {{}},
  "budget_info": {{}},
  "timeline": {{}},
  "contact_info": {{}},
  "hidden_requirements": {{}}
}}
"""
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY", "")}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 2000,
                'temperature': 0.1
            },
            timeout=60
        )
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            try:
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = ai_response[start_idx:end_idx]
                    return json.loads(json_str)
            except:
                pass
                
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
    
    return {}

def extract_all_conditions_with_ai(policy_data: dict) -> dict:
    """숨겨진 조건까지 모두 추출"""
    if not requests:
        return {}
    
    try:
        prompt = f"""
이 정책에서 지원 대상이 되기 위한 모든 조건을 추출해주세요. 명시적 조건부터 암시적 조건까지 모두 포함해주세요.

정책 데이터:
{json.dumps(policy_data, ensure_ascii=False)[:8000]}

추출해야 할 조건 유형:
- 나이 제한
- 지역 제한  
- 소득 수준
- 기업 규모/업력
- 업종/분야
- 학력/자격
- 기타 자격 요건
- 제외 사항
- 우선 순위

JSON 형식으로 응답:
{{
  "age_requirements": [],
  "location_requirements": [],
  "income_requirements": [],
  "business_requirements": [],
  "industry_requirements": [],
  "education_requirements": [],
  "other_requirements": [],
  "exclusions": [],
  "priorities": []
}}
"""
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY", "")}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 1500,
                'temperature': 0.1
            },
            timeout=60
        )
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            try:
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = ai_response[start_idx:end_idx]
                    return json.loads(json_str)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Condition extraction error: {e}")
    
    return {}

def calculate_completeness_score(data: dict) -> float:
    """데이터 완성도 점수 계산"""
    required_fields = ['title', 'description', 'agency', 'target_info', 'support_content']
    optional_fields = ['detail_page_html', 'ai_analysis', 'extracted_conditions']
    
    required_score = sum(1 for field in required_fields if data.get(field)) / len(required_fields)
    optional_score = sum(1 for field in optional_fields if data.get(field)) / len(optional_fields)
    
    return (required_score * 0.7 + optional_score * 0.3) * 100

def fetch_government_policies_with_details(api_key: str) -> list:
        
    except Exception as e:
        logger.error(f"S3 save error for policy {policy_data.get('policy_id', 'unknown')}: {e}")
        return ''

def sync_policies():
    """정책 동기화 - 공공데이터 포털 API 연동 + 임베딩 + OpenSearch"""
    try:
        # API 키 설정
        api_key = os.environ.get('GOV_API_KEY', '0259O7/...==')
        
        # API 데이터 수집 및 개별 사업 처리
        raw_policies = fetch_government_policies_with_details(api_key)
        
        processed_policies = []
        s3_locations = []
        
        for policy in raw_policies:
            # 각 사업별로 완전한 데이터 수집
            complete_policy = collect_complete_policy_data(policy)
            
            # S3에 모든 정보 저장
            s3_key = save_single_policy_to_s3(complete_policy, timestamp)
            if s3_key:
                s3_locations.append(s3_key)
            
            processed_policies.append(complete_policy)
        
        # 임베딩 생성 및 OpenSearch 저장
        indexed_count = process_and_index_policies(processed_policies)
        
        # DynamoDB에 모든 정보 저장
        saved_count = save_complete_policies_to_db(processed_policies)
        
        result = {
            "message": "완전한 데이터 파이프라인 완료",
            "total_policies": len(processed_policies),
            "s3_saved_policies": len(s3_locations),
            "db_saved": saved_count,
            "opensearch_indexed": indexed_count,
            "s3_locations": s3_locations[:5],  # 처음 5개만 표시
            "timestamp": timestamp
        }
        
        logger.info("Policy sync completed", extra=result)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Sync policies error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}, ensure_ascii=False)
        }

def fetch_government_policies(api_key: str) -> list:
    """K-Startup API에서 정책 데이터 가져오기"""
    if not requests:
        return get_sample_policies()
    
    try:
        # K-Startup API URL (올바른 형식)
        base_url = "https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/getBusinessInformation"
        service_key = "0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA=="
        
        # 쿼리 파라미터로 API 호출
        params = {
            'serviceKey': service_key,
            'numOfRows': 50,  # 최대 50개 조회
            'pageNo': 1
        }
        
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            # AI 기반 동적 파싱
            return parse_any_api_response(response.text, 'xml')
        else:
            logger.warning(f"K-Startup API call failed: {response.status_code}")
            logger.warning(f"Response: {response.text[:200]}")
            return get_sample_policies()
            
    except Exception as e:
        logger.error(f"K-Startup API fetch error: {e}")
        return get_sample_policies()

def get_sample_policies() -> list:
    """샘플 정책 데이터"""
    return [
        {
            "policy_id": "sample_001",
            "title": "청년창업지원사업",
            "description": "만 39세 이하 청년의 창업을 지원하는 사업",
            "agency": "중소벤처기업부",
            "target_age": "39세 이하",
            "support_type": "창업지원",
            "region": "전국"
        },
        {
            "policy_id": "sample_002",
            "title": "중소기업 성장지원금",
            "description": "중소기업의 성장을 위한 자금 지원",
            "agency": "중소기업청",
            "target_age": "전 연령",
            "support_type": "자금지원",
            "region": "전국"
        },
        {
            "policy_id": "sample_003",
            "title": "서울시 청년주거지원",
            "description": "서울시 거주 청년의 주거비 지원",
            "agency": "서울시",
            "target_age": "35세 이하",
            "support_type": "주거지원",
            "region": "서울"
        }
    ]

def parse_any_api_response(api_data: str, source_type: str = 'xml') -> list:
    """AI 기반 동적 API 응답 파싱 - 모든 스키마 자동 처리"""
    try:
        # 1단계: 원본 데이터 구조 분석
        raw_structure = analyze_data_structure(api_data, source_type)
        
        # 2단계: AI로 정책 정보 추출
        policies = ai_extract_policies(api_data, raw_structure)
        
        # 3단계: 상세 페이지 크롤링
        for policy in policies:
            if policy.get('detail_url'):
                detail_info = crawl_detail_page(policy['detail_url'])
                # AI로 상세 정보도 구조화
                structured_detail = ai_structure_detail_info(detail_info)
                policy.update(structured_detail)
        
        logger.info(f"AI parsed {len(policies)} policies from {source_type} data")
        return policies if policies else get_sample_policies()
        
    except Exception as e:
        logger.error(f"AI parsing error: {e}")
        return get_sample_policies()

def analyze_data_structure(data: str, data_type: str) -> dict:
    """데이터 구조 자동 분석"""
    try:
        if data_type == 'xml':
            import xml.etree.ElementTree as ET
            root = ET.fromstring(data)
            
            # XML 구조 분석
            structure = {
                'type': 'xml',
                'root_tag': root.tag,
                'item_path': find_item_elements(root),
                'all_fields': extract_all_xml_fields(root),
                'sample_item': get_sample_xml_item(root)
            }
            
        elif data_type == 'json':
            import json
            data_obj = json.loads(data)
            structure = {
                'type': 'json',
                'keys': list(data_obj.keys()) if isinstance(data_obj, dict) else [],
                'sample_data': str(data_obj)[:1000]
            }
        else:
            structure = {'type': 'unknown', 'raw_data': data[:1000]}
            
        return structure
        
    except Exception as e:
        logger.error(f"Structure analysis error: {e}")
        return {'type': 'error', 'raw_data': data[:500]}

def ai_extract_policies(raw_data: str, structure: dict) -> list:
    """AI로 정책 정보 추출 - GPT 활용"""
    try:
        if not requests:
            return fallback_parse_xml(raw_data)
        
        # GPT 프롬프트 생성
        prompt = f"""
다음은 정부 지원사업 API 응답 데이터입니다. 이 데이터에서 정책 정보를 추출해서 JSON 배열로 변환해주세요.

데이터 구조: {structure}

원본 데이터 (처음 2000자):
{raw_data[:2000]}

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
[{"policy_id": "...", "title": "...", ...}]
"""
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY", "")}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 4000,
                'temperature': 0.1
            },
            timeout=60
        )
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            
            # JSON 추출 시도
            try:
                import json
                # JSON 부분만 추출
                start_idx = ai_response.find('[')
                end_idx = ai_response.rfind(']') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = ai_response[start_idx:end_idx]
                    policies = json.loads(json_str)
                    
                    logger.info(f"AI successfully extracted {len(policies)} policies")
                    return policies
                    
            except json.JSONDecodeError as e:
                logger.error(f"AI response JSON parsing error: {e}")
                logger.error(f"AI response: {ai_response[:500]}")
        
        # AI 실패시 폴백
        return fallback_parse_xml(raw_data)
        
    except Exception as e:
        logger.error(f"AI extraction error: {e}")
        return fallback_parse_xml(raw_data)

def fallback_parse_xml(xml_data: str) -> list:
    """AI 실패시 기본 XML 파싱"""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        policies = []
        
        items = root.findall('.//item')
        for i, item in enumerate(items):
            cols = {col.get('name'): col.text for col in item.findall('col')}
            
            policy = {
                'policy_id': f"policy_{i+1}",
                'title': find_title_field(cols),
                'description': find_description_field(cols),
                'raw_data': cols,
                'source': 'fallback_xml'
            }
            policies.append(policy)
            
        return policies
        
    except Exception as e:
        logger.error(f"Fallback parsing error: {e}")
        return get_sample_policies()

def find_title_field(cols: dict) -> str:
    """제목 필드 자동 찾기"""
    title_candidates = ['supt_biz_titl_nm', 'title', 'name', 'biz_nm', 'policy_name']
    for candidate in title_candidates:
        if candidate in cols and cols[candidate]:
            return cols[candidate]
    return list(cols.values())[0] if cols else ''

def find_description_field(cols: dict) -> str:
    """설명 필드 자동 찾기"""
    desc_candidates = ['supt_biz_intrd_info', 'description', 'content', 'biz_cont', 'intro']
    for candidate in desc_candidates:
        if candidate in cols and cols[candidate]:
            return cols[candidate]
    return ''

def ai_structure_detail_info(detail_info: dict) -> dict:
    """상세 정보 AI 구조화"""
    if not detail_info or not requests:
        return detail_info
    
    try:
        prompt = f"""
다음은 크롤링한 정책 상세 페이지 정보입니다. 이를 구조화된 JSON으로 정리해주세요:

{detail_info}

다음 필드들로 구조화해주세요:
- application_method: 신청 방법
- application_period: 신청 기간  
- eligibility: 신청 자격
- required_documents: 필요 서류
- selection_criteria: 선정 기준
- contact_info: 문의처
- support_details: 지원 상세 내용

JSON 형식으로만 응답:
{{"application_method": "...", "application_period": "...", ...}}
"""
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY", "")}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 1000,
                'temperature': 0.1
            },
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json()['choices'][0]['message']['content']
            try:
                import json
                start_idx = ai_response.find('{')
                end_idx = ai_response.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = ai_response[start_idx:end_idx]
                    return json.loads(json_str)
            except:
                pass
                
    except Exception as e:
        logger.error(f"AI detail structuring error: {e}")
    
    return detail_info

def find_item_elements(root) -> str:
    """아이템 요소 경로 찾기"""
    for elem in root.iter():
        if elem.tag.lower() in ['item', 'data', 'record', 'row']:
            return f".//{elem.tag}"
    return ".//item"

def extract_all_xml_fields(root) -> list:
    """모든 XML 필드 추출"""
    fields = set()
    for elem in root.iter():
        if elem.get('name'):
            fields.add(elem.get('name'))
        if elem.tag not in ['results', 'data', 'item', 'col']:
            fields.add(elem.tag)
    return list(fields)

def get_sample_xml_item(root) -> dict:
    """샘플 XML 아이템 가져오기"""
    items = root.findall('.//item')
    if items:
        cols = {col.get('name'): col.text for col in items[0].findall('col')}
        return cols
    return {}

def extract_age_info(content: str) -> str:
    """내용에서 나이 정보 추출"""
    import re
    
    # 나이 관련 패턴 찾기
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
    
    # 청년 키워드 찾기
    if '청년' in content:
        return '39세 이하'
    
    return '전 연령'

def extract_budget_amount(budget_info: str) -> str:
    """예산 정보에서 금액 추출"""
    import re
    
    # 금액 패턴 찾기
    amount_patterns = [
        r'(\d+(?:\.\d+)?)억원',
        r'(\d+)백만원',
        r'(\d+)조원',
        r'최대\s*(\d+(?:\.\d+)?)억원',
        r'최대\s*(\d+)백만원'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, budget_info)
        if match:
            return match.group(0)
    
    return budget_info[:50] if budget_info else ''

def extract_region_info(target_info: str) -> str:
    """대상 정보에서 지역 정보 추출"""
    regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
    
    for region in regions:
        if region in target_info:
            return region
    
    return '전국'

def crawl_detail_page(detail_url: str) -> dict:
    """상세 페이지 크롤링"""
    if not requests or not detail_url:
        return {}
    
    try:
        # K-Startup 도메인 추가
        if not detail_url.startswith('http'):
            detail_url = f"https://{detail_url}"
        
        response = requests.get(detail_url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 상세 정보 추출
            detail_info = {
                'application_method': extract_text_by_keywords(soup, ['신청방법', '신청절차']),
                'application_period': extract_text_by_keywords(soup, ['신청기간', '접수기간']),
                'selection_criteria': extract_text_by_keywords(soup, ['선정기준', '평가기준']),
                'required_documents': extract_text_by_keywords(soup, ['제출서류', '신청서류']),
                'contact_info': extract_text_by_keywords(soup, ['문의처', '연락처', '담당자']),
                'eligibility': extract_text_by_keywords(soup, ['지원자격', '신청자격']),
                'support_details': extract_text_by_keywords(soup, ['지원내용', '지원현황']),
                'full_text': soup.get_text()[:2000]  # 전체 텍스트 일부
            }
            
            return detail_info
            
    except Exception as e:
        logger.error(f"Detail page crawling error for {detail_url}: {e}")
        return {}
    
    return {}

def extract_text_by_keywords(soup, keywords: list) -> str:
    """키워드 기반 텍스트 추출"""
    try:
        for keyword in keywords:
            # 키워드를 포함한 요소 찾기
            elements = soup.find_all(text=lambda text: text and keyword in text)
            if elements:
                # 부모 요소의 텍스트 추출
                for element in elements:
                    parent = element.parent
                    if parent:
                        text = parent.get_text().strip()
                        if len(text) > 10:  # 의미있는 내용만
                            return text[:500]  # 최대 500자
        return ''
    except:
        return ''

def save_policies_to_db(policies: list) -> int:
    """정책 데이터를 DynamoDB에 저장 - 모든 필드 포함"""
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('PoliciesTable')  # 올바른 테이블명
        
        saved_count = 0
        for policy in policies:
            # 모든 정보를 포함한 아이템 생성
            item = {
                'policy_id': policy['policy_id'],
                'title': policy.get('title', ''),
                'description': policy.get('description', ''),
                'characteristics': policy.get('characteristics', ''),
                'support_content': policy.get('support_content', ''),
                'target_info': policy.get('target_info', ''),
                'budget_info': policy.get('budget_info', ''),
                'category_code': policy.get('category_code', ''),
                'detail_url': policy.get('detail_url', ''),
                'biz_year': policy.get('biz_year', '2025'),
                'agency': policy.get('agency', 'K-Startup'),
                'target_age': policy.get('target_age', ''),
                'support_amount': policy.get('support_amount', ''),
                'region': policy.get('region', ''),
                'source': 'kstartup_api',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # 상세 페이지 정보 추가 (있는 경우)
            detail_fields = ['application_method', 'application_period', 'selection_criteria', 
                           'required_documents', 'contact_info', 'eligibility', 'support_details']
            
            for field in detail_fields:
                if policy.get(field):
                    item[field] = policy[field]
            
            # DynamoDB에 저장
            table.put_item(Item=item)
            saved_count += 1
            
            logger.info(f"Saved policy: {policy.get('title', '')[:50]}...")
        
        return saved_count
        
    except Exception as e:
        logger.error(f"DB save error: {e}")
        return 0

def process_and_index_policies(policies):
    """정책 데이터 임베딩 생성 및 OpenSearch 인덱싱"""
    try:
        # OpenSearch 클라이언트 설정
        opensearch_client = get_opensearch_client()
        
        indexed_count = 0
        for policy in policies:
            # 임베딩 생성
            embedding = generate_embedding(policy)
            
            # OpenSearch 문서 준비
            doc = {
                'policy_id': policy['policy_id'],
                'title': policy['title'],
                'description': policy['description'],
                'agency': policy['agency'],
                'target_age': policy['target_age'],
                'support_type': policy['support_type'],
                'region': policy['region'],
                'embedding': embedding,
                'created_at': '2025-01-14'
            }
            
            # OpenSearch에 인덱싱
            opensearch_client.index(
                index='policies',
                id=policy['policy_id'],
                body=doc
            )
            indexed_count += 1
            
        return indexed_count
        
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        return 0

def get_opensearch_client():
    """인증된 OpenSearch 클라이언트 생성"""
    host = os.environ.get('OPENSEARCH_HOST', 'https://xv4xqd9c2ttr1a9vl23k.us-east-1.aoss.amazonaws.com')
    region = 'us-east-1'
    service = 'aoss'
    
    credentials = boto3.Session().get_credentials()
    auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    client = OpenSearch(
        hosts=[{'host': host.replace('https://', ''), 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
    return client

def generate_embedding(policy):
    """정책 데이터로 임베딩 벡터 생성 - 모든 정보 활용"""
    try:
        # 모든 정보를 결합한 포괄적 텍스트 생성
        text_parts = [
            policy.get('title', ''),
            policy.get('description', ''),
            policy.get('characteristics', ''),
            policy.get('support_content', ''),
            policy.get('target_info', ''),
            policy.get('budget_info', ''),
            policy.get('application_method', ''),
            policy.get('eligibility', ''),
            policy.get('support_details', '')
        ]
        
        # 빈 문자열 제거 및 결합
        full_text = ' '.join([part for part in text_parts if part and part.strip()])
        
        # 텍스트 길이 제한 (OpenAI 토큰 제한 고려)
        if len(full_text) > 8000:
            full_text = full_text[:8000]
        
        logger.info(f"Generating embedding for policy: {policy.get('title', '')[:50]}...")
        
        if requests:
            response = requests.post(
                'https://api.openai.com/v1/embeddings',
                headers={
                    'Authorization': f'Bearer {os.environ.get("OPENAI_API_KEY", "")}',
                    'Content-Type': 'application/json'
                },
                json={
                    'input': full_text,
                    'model': 'text-embedding-3-small'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                embedding = response.json()['data'][0]['embedding']
                logger.info(f"Successfully generated {len(embedding)}-dimensional embedding")
                return embedding
            else:
                logger.warning(f"OpenAI API error: {response.status_code} - {response.text}")
        
        # 기본 더미 벡터 (1536차원)
        return [0.0] * 1536
        
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        return [0.0] * 1536

def search_external(keyword):
    """외부 API 검색"""
    try:
        if not keyword:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "키워드가 필요합니다"})
            }
        
        # 간단한 테스트 응답
        policies = [
            {
                "id": "ext_001",
                "title": f"{keyword} 관련 지원사업 1",
                "description": f"{keyword}을 위한 정부 지원사업",
                "agency": "중소벤처기업부"
            },
            {
                "id": "ext_002", 
                "title": f"{keyword} 관련 지원사업 2",
                "description": f"{keyword} 분야 성장 지원",
                "agency": "산업통상자원부"
            }
        ]
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "keyword": keyword,
                "policies": policies,
                "note": "공공데이터 API 연동 구현 중"
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Search external error: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "외부 검색 중 오류가 발생했습니다"})
        }