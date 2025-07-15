"""
OpenSearch 인덱스 설정 및 매핑 생성
"""

import json
import boto3
import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from aws_lambda_powertools import Logger

logger = Logger()

def handler(event, context):
    """OpenSearch 인덱스 설정 핸들러"""
    try:
        action = event.get('action', 'create_index')
        
        if action == 'create_index':
            return create_policies_index()
        elif action == 'delete_index':
            return delete_policies_index()
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid action'})
            }
            
    except Exception as e:
        logger.error(f"OpenSearch setup error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def create_policies_index():
    """정책 인덱스 생성"""
    try:
        client = get_opensearch_client()
        
        # 인덱스 매핑 정의
        index_mapping = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                }
            },
            "mappings": {
                "properties": {
                    "policy_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "agency": {"type": "keyword"},
                    "target_age": {"type": "text"},
                    "support_type": {"type": "keyword"},
                    "region": {"type": "keyword"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": 1536,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                        }
                    },
                    "created_at": {"type": "date"}
                }
            }
        }
        
        # 인덱스 생성
        if client.indices.exists(index="policies"):
            logger.info("Index already exists")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': '인덱스가 이미 존재합니다',
                    'index': 'policies'
                })
            }
        
        response = client.indices.create(
            index="policies",
            body=index_mapping
        )
        
        logger.info("Index created successfully", extra={"response": response})
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '인덱스가 성공적으로 생성되었습니다',
                'index': 'policies',
                'response': response
            })
        }
        
    except Exception as e:
        logger.error(f"Index creation error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'인덱스 생성 실패: {str(e)}'})
        }

def delete_policies_index():
    """정책 인덱스 삭제"""
    try:
        client = get_opensearch_client()
        
        if not client.indices.exists(index="policies"):
            return {
                'statusCode': 404,
                'body': json.dumps({'message': '인덱스가 존재하지 않습니다'})
            }
        
        response = client.indices.delete(index="policies")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '인덱스가 삭제되었습니다',
                'response': response
            })
        }
        
    except Exception as e:
        logger.error(f"Index deletion error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'인덱스 삭제 실패: {str(e)}'})
        }

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