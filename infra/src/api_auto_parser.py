import json
import re
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import openai

def parse_api_info_with_ai(api_info: str) -> Dict:
    """AI를 사용해 API 정보를 자동 파싱"""
    
    prompt = f"""
다음 API 정보를 분석해서 JSON 형태로 구조화해주세요:

{api_info}

다음 형식으로 응답해주세요:
{{
    "name": "API 서비스명",
    "url": "API 엔드포인트 URL",
    "method": "GET 또는 POST",
    "auth_type": "serviceKey, apiKey, bearer, 또는 none",
    "auth_key": "인증키 값",
    "response_format": "xml 또는 json",
    "default_params": {{"param1": "value1"}},
    "headers": {{"header1": "value1"}}
}}

인증키가 여러 개 있으면 가장 적절한 것을 선택하고, URL에서 도메인과 경로를 정확히 추출해주세요.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        result = response.choices[0].message.content
        # JSON 부분만 추출
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
    except Exception as e:
        print(f"AI 파싱 오류: {e}")
    
    # AI 실패시 정규식 백업 파싱
    return fallback_parse(api_info)

def fallback_parse(api_info: str) -> Dict:
    """정규식 기반 백업 파싱"""
    
    # URL 추출
    url_patterns = [
        r'https?://[^\s]+',
        r'URL[:\s]*([^\s\n]+)',
        r'엔드포인트[:\s]*([^\s\n]+)'
    ]
    
    url = None
    for pattern in url_patterns:
        match = re.search(pattern, api_info, re.IGNORECASE)
        if match:
            url = match.group(1) if match.groups() else match.group()
            break
    
    # 인증키 추출
    key_patterns = [
        r'serviceKey[=:\s]*([^\s&\n]+)',
        r'인증키[:\s]*([^\s\n]+)',
        r'API[_\s]*KEY[:\s]*([^\s\n]+)',
        r'키[:\s]*([^\s\n]+)'
    ]
    
    auth_key = None
    for pattern in key_patterns:
        match = re.search(pattern, api_info, re.IGNORECASE)
        if match:
            auth_key = match.group(1)
            break
    
    # 서비스명 추출
    name_patterns = [
        r'서비스명[:\s]*([^\n]+)',
        r'API[_\s]*명[:\s]*([^\n]+)',
        r'제목[:\s]*([^\n]+)'
    ]
    
    name = "자동등록 API"
    for pattern in name_patterns:
        match = re.search(pattern, api_info, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            break
    
    return {
        "name": name,
        "url": url,
        "method": "GET",
        "auth_type": "serviceKey" if auth_key else "none",
        "auth_key": auth_key,
        "response_format": "xml" if "xml" in api_info.lower() else "json",
        "default_params": {"numOfRows": "50", "pageNo": "1"},
        "headers": {}
    }

def test_api_configurations(parsed_info: Dict) -> Dict:
    """여러 설정으로 API 테스트"""
    
    test_configs = [
        # 기본 설정
        parsed_info,
        
        # serviceKey 파라미터 방식
        {**parsed_info, "auth_type": "serviceKey"},
        
        # API Key 헤더 방식  
        {**parsed_info, "auth_type": "apiKey", "headers": {"X-API-Key": parsed_info.get("auth_key")}},
        
        # Bearer 토큰 방식
        {**parsed_info, "auth_type": "bearer", "headers": {"Authorization": f"Bearer {parsed_info.get('auth_key')}"}}
    ]
    
    for config in test_configs:
        try:
            result = test_single_api(config)
            if result["success"]:
                return {"success": True, "config": config, "test_result": result}
        except Exception as e:
            continue
    
    return {"success": False, "error": "모든 설정에서 API 테스트 실패"}

def test_single_api(config: Dict) -> Dict:
    """단일 API 설정 테스트"""
    
    url = config["url"]
    method = config.get("method", "GET")
    auth_type = config.get("auth_type", "none")
    auth_key = config.get("auth_key")
    params = config.get("default_params", {})
    headers = config.get("headers", {})
    
    # 인증 설정
    if auth_type == "serviceKey" and auth_key:
        params["serviceKey"] = auth_key
    elif auth_type == "apiKey" and auth_key:
        headers["X-API-Key"] = auth_key
    elif auth_type == "bearer" and auth_key:
        headers["Authorization"] = f"Bearer {auth_key}"
    
    # API 호출
    if method.upper() == "GET":
        response = requests.get(url, params=params, headers=headers, timeout=10)
    else:
        response = requests.post(url, data=params, headers=headers, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}")
    
    # 응답 파싱
    content = response.text
    record_count = 0
    
    if config.get("response_format") == "xml":
        try:
            root = ET.fromstring(content)
            items = root.findall('.//item')
            record_count = len(items)
        except:
            pass
    else:
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                # 일반적인 응답 구조에서 데이터 개수 추출
                for key in ['items', 'data', 'results', 'records']:
                    if key in data and isinstance(data[key], list):
                        record_count = len(data[key])
                        break
        except:
            pass
    
    return {
        "success": True,
        "recordCount": record_count,
        "responseSize": len(content),
        "contentType": response.headers.get("content-type", "")
    }

def auto_register_api(api_info: str) -> Dict:
    """API 정보 자동 등록 메인 함수"""
    
    try:
        # 1. AI로 API 정보 파싱
        parsed_info = parse_api_info_with_ai(api_info)
        
        if not parsed_info.get("url"):
            return {"success": False, "error": "API URL을 찾을 수 없습니다."}
        
        # 2. 여러 설정으로 테스트
        test_result = test_api_configurations(parsed_info)
        
        if not test_result["success"]:
            return test_result
        
        # 3. 성공한 설정으로 DynamoDB에 저장
        api_config = test_result["config"]
        api_id = f"auto_{hash(api_config['url']) % 100000}"
        
        # DynamoDB 저장 로직 (실제 구현 필요)
        save_api_config(api_id, api_config)
        
        return {
            "success": True,
            "api": {
                "id": api_id,
                "name": api_config["name"],
                "url": api_config["url"]
            },
            "testResult": test_result["test_result"]
        }
        
    except Exception as e:
        return {"success": False, "error": f"등록 실패: {str(e)}"}

def save_api_config(api_id: str, config: Dict):
    """API 설정을 DynamoDB에 저장"""
    # 실제 DynamoDB 저장 로직 구현
    pass