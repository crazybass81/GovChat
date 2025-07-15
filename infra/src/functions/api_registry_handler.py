"""
동적 API 레지스트리 시스템 - 여러 정부 API 자동 관리
"""

import json
import boto3
import os
from datetime import datetime
from aws_lambda_powertools import Logger

logger = Logger()

def handler(event, context):
    """API 레지스트리 관리 핸들러"""
    try:
        # GET 요청 처리
        if event.get('httpMethod') == 'GET':
            action = event.get('queryStringParameters', {}).get('action', 'list')
        else:
            # POST 요청 처리
            body = json.loads(event.get('body', '{}'))
            action = body.get('action', 'list')
        
        if action == 'list':
            return list_registered_apis()
        elif action == 'add':
            api_config = body.get('api_config') if 'body' in locals() else None
            return add_api(api_config)
        elif action == 'auto_register':
            api_info = body.get('apiInfo') if 'body' in locals() else None
            return auto_register_api(api_info)
        elif action == 'sync_all':
            return sync_all_apis()
        elif action == 'test':
            api_id = body.get('api_id') if 'body' in locals() else None
            return test_api(api_id)
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid action'})
            }
            
    except Exception as e:
        logger.error(f"API registry error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def get_default_api_registry() -> dict:
    """기본 API 레지스트리"""
    return {
        'kstartup': {
            'api_id': 'kstartup',
            'name': 'K-Startup 창업지원사업',
            'base_url': 'https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/getBusinessInformation',
            'method': 'GET',
            'response_format': 'xml',
            'auth_type': 'service_key',
            'service_key': '0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA==',
            'params': {
                'numOfRows': 50,
                'pageNo': 1
            },
            'active': True,
            'last_sync': None
        },
        'sba': {
            'api_id': 'sba',
            'name': '소상공인시장진흥공단',
            'base_url': 'https://openapi.semas.or.kr/api/service/rest/getBizInfo',
            'method': 'GET',
            'response_format': 'xml',
            'auth_type': 'service_key',
            'service_key': 'YOUR_SBA_API_KEY',
            'params': {
                'numOfRows': 100,
                'pageNo': 1
            },
            'active': False,
            'last_sync': None
        }
    }

def list_registered_apis():
    """등록된 API 목록 조회"""
    try:
        api_registry = get_default_api_registry()
        
        api_list = []
        for api_id, config in api_registry.items():
            api_list.append({
                'api_id': api_id,
                'name': config.get('name', ''),
                'active': config.get('active', False),
                'last_sync': config.get('last_sync'),
                'base_url': config.get('base_url', '')
            })
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'total_apis': len(api_list),
                'active_apis': len([a for a in api_list if a['active']]),
                'apis': api_list
            })
        }
        
    except Exception as e:
        logger.error(f"List APIs error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def add_api(api_config: dict):
    """새 API 등록"""
    try:
        if not api_config or not api_config.get('api_id'):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invalid API config'})
            }
        
        # 기본값 설정
        api_config.setdefault('active', False)
        api_config.setdefault('created_at', datetime.utcnow().isoformat())
        api_config.setdefault('last_sync', None)
        
        logger.info(f"API {api_config['api_id']} registered successfully")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': f'API {api_config["api_id"]} registered successfully',
                'api_config': api_config
            })
        }
        
    except Exception as e:
        logger.error(f"Add API error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def sync_all_apis():
    """모든 등록된 API 동기화"""
    try:
        api_registry = get_default_api_registry()
        results = {}
        
        for api_id, api_config in api_registry.items():
            if api_config.get('active', False):
                logger.info(f"Syncing API: {api_id}")
                result = sync_single_api(api_config)
                results[api_id] = result
            else:
                results[api_id] = {'status': 'skipped', 'reason': 'inactive'}
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': f'Synced {len([r for r in results.values() if r.get("status") == "success"])} APIs',
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Sync all APIs error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def sync_single_api(api_config: dict) -> dict:
    """개별 API 동기화"""
    try:
        # API 호출
        response = call_api(api_config)
        
        if not response:
            return {'status': 'error', 'message': 'API call failed'}
        
        # AI 파싱
        from external_data_sync_handler import parse_any_api_response
        policies = parse_any_api_response(response, api_config['response_format'])
        
        if not policies:
            return {'status': 'error', 'message': 'No policies parsed'}
        
        # 각 정책별 완전한 데이터 수집 및 S3 저장
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        saved_count = 0
        
        for policy in policies:
            # API 소스 정보 추가
            policy['api_source'] = api_config['api_id']
            policy['api_name'] = api_config['name']
            
            # 완전한 데이터 수집
            from external_data_sync_handler import collect_complete_policy_data, save_single_policy_to_s3
            complete_policy = collect_complete_policy_data(policy)
            
            # S3 저장
            s3_key = save_single_policy_to_s3(complete_policy, timestamp)
            if s3_key:
                saved_count += 1
        
        return {
            'status': 'success',
            'policies_count': len(policies),
            'saved_count': saved_count,
            'timestamp': timestamp
        }
        
    except Exception as e:
        logger.error(f"Single API sync error for {api_config.get('api_id', 'unknown')}: {e}")
        return {'status': 'error', 'message': str(e)}

def call_api(api_config: dict) -> str:
    """동적 API 호출"""
    try:
        import requests
        
        url = api_config['base_url']
        method = api_config.get('method', 'GET').upper()
        
        # 인증 설정
        params = api_config.get('params', {}).copy()
        headers = api_config.get('headers', {}).copy()
        
        if api_config.get('auth_type') == 'service_key':
            params['serviceKey'] = api_config.get('service_key')
        elif api_config.get('auth_type') == 'api_key':
            headers['Authorization'] = f"Bearer {api_config.get('api_key')}"
        
        # API 호출
        if method == 'GET':
            response = requests.get(url, params=params, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=params, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == 200:
            return response.text
        else:
            logger.warning(f"API call failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"API call error: {e}")
        return None

def auto_register_api(api_info: str):
    """API 정보 자동 등록"""
    try:
        from api_auto_parser import auto_register_api as parse_and_register
        
        result = parse_and_register(api_info)
        
        return {
            'statusCode': 200 if result['success'] else 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Auto register API error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'success': False, 'error': str(e)})
        }

def test_api(api_id: str):
    """API 연결 테스트"""
    try:
        api_registry = get_default_api_registry()
        
        if api_id not in api_registry:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': f'API {api_id} not found'})
            }
        
        api_config = api_registry[api_id]
        response = call_api(api_config)
        
        if response:
            result = {
                'api_id': api_id,
                'status': 'success',
                'response_length': len(response),
                'response_format': api_config.get('response_format'),
                'sample_response': response[:500] + '...' if len(response) > 500 else response
            }
        else:
            result = {
                'api_id': api_id,
                'status': 'failed',
                'message': 'No response received'
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Test API error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }