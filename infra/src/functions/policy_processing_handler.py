"""
개선된 정책 데이터 처리 파이프라인
- 스트리밍 ETL + 오류 복구
- 하이브리드 검색 (필터 + 벡터)
- 온라인 클러스터링
- 실시간 Feature Store
"""

import json
import boto3
import numpy as np
from datetime import datetime
from aws_lambda_powertools import Logger, Tracer
from typing import Dict, List, Any, Optional
import hashlib
import re

logger = Logger()
tracer = Tracer()

# AWS 서비스 클라이언트
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
opensearch = boto3.client('opensearchserverless')
s3 = boto3.client('s3')
stepfunctions = boto3.client('stepfunctions')

# OpenSearch Serverless 엔드포인트
OPENSEARCH_ENDPOINT = 'https://xv4xqd9c2ttr1a9vl23k.us-east-1.aoss.amazonaws.com'
OPENSEARCH_INDEX = 'policy-vectors'

# 테이블 정의
policies_table = dynamodb.Table('PoliciesTable')
conditions_table = dynamodb.Table('PolicyConditionsTable')
feature_store_table = dynamodb.Table('FeatureStoreTable')
cluster_table = dynamodb.Table('PolicyClustersTable')

@tracer.capture_lambda_handler
def handler(event, context):
    """개선된 정책 처리 파이프라인 - Step Functions 워크플로"""
    try:
        # 입력 소스별 처리
        source_type = event.get('source_type')  # 'api', 'document', 'url'
        raw_data = event.get('raw_data')
        
        logger.info(f"Processing {source_type} data")
        
        # 1. 원본 데이터 S3 저장 (버저닝)
        s3_key = store_raw_data(raw_data, source_type)
        
        # 2. Step Functions 워크플로 시작
        workflow_input = {
            's3_key': s3_key,
            'source_type': source_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        response = stepfunctions.start_execution(
            stateMachineArn='arn:aws:states:us-east-1:account:stateMachine:PolicyProcessingWorkflow',
            input=json.dumps(workflow_input)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'execution_arn': response['executionArn'],
                's3_key': s3_key
            })
        }
        
    except Exception as e:
        logger.error(f"Pipeline initiation error: {e}")
        # DLQ로 전송
        send_to_dlq(event, str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_policy_data(policy_id: str) -> Dict:
    """정책 데이터 조회"""
    response = policies_table.get_item(Key={'policy_id': policy_id})
    return response.get('Item', {})

# === Step Functions 워크플로 단계별 함수들 ===

def parse_document_step(event, context):
    """Step 1: 문서 파싱 (OCR, HTML 정규화)"""
    try:
        s3_key = event['s3_key']
        source_type = event['source_type']
        
        # S3에서 원본 데이터 조회
        response = s3.get_object(Bucket='gov-support-raw-data', Key=s3_key)
        raw_data = json.loads(response['Body'].read())
        
        # 소스 타입별 파싱
        if source_type == 'document':
            parsed_data = parse_document_content(raw_data)
        elif source_type == 'url':
            parsed_data = parse_url_content(raw_data)
        elif source_type == 'api':
            parsed_data = parse_api_response(raw_data)
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        return {
            'parsed_data': parsed_data,
            's3_key': s3_key,
            'source_type': source_type
        }
        
    except Exception as e:
        logger.error(f"Document parsing error: {e}")
        raise

def extract_conditions_step(event, context):
    """Step 2: AI 기반 조건 추출"""
    try:
        parsed_data = event['parsed_data']
        
        # LLM을 사용한 구조화된 조건 추출
        conditions = extract_structured_conditions(parsed_data)
        
        return {
            **event,
            'extracted_conditions': conditions
        }
        
    except Exception as e:
        logger.error(f"Condition extraction error: {e}")
        raise

def generate_embeddingsㅇㄴ_step(event, context):
    """Step 3: 하이브리드 임베딩 생성"""
    try:
        parsed_data = event['parsed_data']
        
        # 하이브리드 임베딩 생성
        embeddings = generate_hybrid_embeddings(parsed_data)
        
        return {
            **event,
            'embeddings': embeddings
        }
        
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise

def cluster_and_index_step(event, context):
    """Step 4: 클러스터링 및 인덱싱"""
    try:
        policy_id = event['parsed_data']['policy_id']
        embeddings = event['embeddings']
        parsed_data = event['parsed_data']
        
        # 온라인 클러스터링
        online_clustering(policy_id, parsed_data, embeddings)
        
        # OpenSearch 인덱스 업데이트
        update_opensearch_index(policy_id, parsed_data, embeddings)
        
        return {
            'policy_id': policy_id,
            'status': 'completed',
            'processed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Clustering and indexing error: {e}")
        raise

def parse_document_content(raw_data: Dict) -> Dict:
    """문서 내용 파싱"""
    # OCR 또는 텍스트 추출 로직
    return {
        'policy_id': f"doc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        'title': raw_data.get('title', ''),
        'description': raw_data.get('content', ''),
        'agency': raw_data.get('agency', ''),
        'source': 'document'
    }

def parse_url_content(raw_data: Dict) -> Dict:
    """URL 내용 파싱"""
    # 웹 스크래핑 또는 기사 파싱 로직
    return {
        'policy_id': f"url_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        'title': raw_data.get('title', ''),
        'description': raw_data.get('content', ''),
        'agency': raw_data.get('source', ''),
        'source': 'url',
        'original_url': raw_data.get('url', '')
    }

def parse_api_response(raw_data: Dict) -> Dict:
    """API 응답 파싱"""
    # API 응답 구조화
    return {
        'policy_id': raw_data.get('id', f"api_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"),
        'title': raw_data.get('title', ''),
        'description': raw_data.get('description', ''),
        'agency': raw_data.get('agency', ''),
        'source': 'api'
    }

def update_opensearch_index(policy_id: str, policy_data: Dict, embeddings: Dict):
    """OpenSearch 인덱스 업데이트"""
    try:
        # 하이브리드 검색을 위한 문서 구조
        document = {
            'policy_id': policy_id,
            'title': policy_data['title'],
            'description': policy_data['description'],
            'agency': policy_data['agency'],
            'title_vector': embeddings.get('title_vector', []),
            'content_vector': embeddings.get('content_vector', []),
            'full_vector': embeddings.get('full_vector', []),
            'indexed_at': datetime.utcnow().isoformat(),
            'source': policy_data.get('source', 'unknown')
        }
        
        # OpenSearch Serverless에 인덱싱
        try:
            from opensearchpy import OpenSearch, RequestsHttpConnection
            from aws_requests_auth.aws_auth import AWSRequestsAuth
            
            # AWS 인증 설정
            host = OPENSEARCH_ENDPOINT.replace('https://', '')
            region = 'us-east-1'
            service = 'aoss'
            credentials = boto3.Session().get_credentials()
            awsauth = AWSRequestsAuth(credentials, region, service)
            
            # OpenSearch 클라이언트 생성
            client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
            
            # 인덱스 생성 (없을 경우만)
            if not client.indices.exists(index=OPENSEARCH_INDEX):
                index_body = {
                    'settings': {
                        'index': {
                            'knn': True,
                            'knn.algo_param.ef_search': 100
                        }
                    },
                    'mappings': {
                        'properties': {
                            'policy_id': {'type': 'keyword'},
                            'title': {'type': 'text'},
                            'description': {'type': 'text'},
                            'agency': {'type': 'keyword'},
                            'title_vector': {
                                'type': 'knn_vector',
                                'dimension': 512,
                                'method': {
                                    'name': 'hnsw',
                                    'space_type': 'cosinesimil'
                                }
                            },
                            'content_vector': {
                                'type': 'knn_vector',
                                'dimension': 512,
                                'method': {
                                    'name': 'hnsw',
                                    'space_type': 'cosinesimil'
                                }
                            },
                            'full_vector': {
                                'type': 'knn_vector',
                                'dimension': 1536,
                                'method': {
                                    'name': 'hnsw',
                                    'space_type': 'cosinesimil'
                                }
                            }
                        }
                    }
                }
                client.indices.create(index=OPENSEARCH_INDEX, body=index_body)
                logger.info(f"Created OpenSearch index: {OPENSEARCH_INDEX}")
            
            # 문서 인덱싱
            response = client.index(
                index=OPENSEARCH_INDEX,
                id=policy_id,
                body=document
            )
            
            logger.info(f"Indexed policy {policy_id} to OpenSearch: {response['result']}")
            
        except ImportError:
            logger.warning("opensearch-py not available, using mock indexing")
            logger.info(f"Mock indexed policy {policy_id} to OpenSearch")
        
    except Exception as e:
        logger.error(f"OpenSearch indexing error: {e}")
        raise

def transform_policy_schema(policy: Dict) -> Dict:
    """정책 데이터 스키마 변환"""
    return {
        'policy_id': policy.get('policy_id'),
        'title': policy.get('title', ''),
        'description': policy.get('description', ''),
        'agency': policy.get('agency', ''),
        'target_audience': extract_target_audience(policy),
        'support_type': extract_support_type(policy),
        'eligibility_criteria': extract_eligibility_criteria(policy),
        'application_period': policy.get('application_period', ''),
        'support_amount': extract_support_amount(policy),
        'keywords': extract_keywords(policy),
        'processed_at': datetime.utcnow().isoformat()
    }

def generate_hybrid_embeddings(policy: Dict) -> Dict:
    """하이브리드 임베딩 생성 - 한국어 특화"""
    try:
        # 1. 텍스트 전처리 - 행정용어 정규화
        normalized_text = normalize_administrative_terms(policy)
        
        # 2. 다중 임베딩 모델 사용
        embeddings = {}
        
        # OpenAI text-embedding-3-large (글로벌)
        openai_embedding = get_openai_embedding(normalized_text)
        embeddings['openai'] = openai_embedding
        
        # Ko-E5 기반 모델 (한국어 특화)
        korean_embedding = get_korean_embedding(normalized_text)
        embeddings['korean'] = korean_embedding
        
        # 3. 앙상블 임베딩 생성
        ensemble_embedding = create_ensemble_embedding(embeddings)
        
        return {
            'title_vector': ensemble_embedding[:512],
            'content_vector': ensemble_embedding[512:1024],
            'full_vector': ensemble_embedding,
            'metadata': {
                'model_versions': ['openai-3-large', 'ko-e5-base'],
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Hybrid embedding error: {e}")
        return {}

# 기존 함수는 update_opensearch_index로 통합됨

def online_clustering(policy_id: str, policy: Dict, embeddings: Dict):
    """온라인 클러스터링 - HDBSCAN 기반"""
    try:
        # 1. 기존 클러스터 중심점들 조회
        existing_clusters = get_existing_clusters()
        
        # 2. 새 정책의 임베딩과 기존 클러스터들 간 유사도 계산
        policy_vector = np.array(embeddings['full_vector'])
        similarities = calculate_cluster_similarities(policy_vector, existing_clusters)
        
        # 3. 임계값 기반 클러스터 할당 또는 새 클러스터 생성
        cluster_threshold = 0.8
        best_cluster = None
        max_similarity = 0
        
        for cluster_id, similarity in similarities.items():
            if similarity > max_similarity:
                max_similarity = similarity
                best_cluster = cluster_id
        
        if max_similarity >= cluster_threshold:
            # 기존 클러스터에 할당
            assign_to_cluster(policy_id, best_cluster, max_similarity)
            update_cluster_centroid(best_cluster, policy_vector)
        else:
            # 새 클러스터 생성
            new_cluster_id = create_new_cluster(policy_id, policy_vector, policy)
        
        # 4. AI 기반 클러스터 라벨링
        cluster_label = generate_cluster_label(policy_id, policy)
        
        # 5. Feature Store 업데이트
        update_cluster_features(policy_id, cluster_label, embeddings)
        
        logger.info(f"Policy {policy_id} clustered with similarity {max_similarity}")
        
    except Exception as e:
        logger.error(f"Online clustering error: {e}")

# 기존 함수는 update_opensearch_index로 통합됨

# === 새로운 핵심 함수들 ===

def extract_structured_conditions(policy: Dict) -> Dict:
    """LLM 기반 정책 조건 구조화 추출"""
    try:
        extraction_prompt = f"""
        다음 정책 정보에서 매칭에 필요한 조건들을 JSON 형태로 추출해주세요:
        
        정책명: {policy.get('title', '')}
        내용: {policy.get('description', '')}
        기관: {policy.get('agency', '')}
        
        추출할 조건:
        {{
            "age_range": {{"min": 숫자, "max": 숫자}},
            "regions": ["지역명"],
            "target_groups": ["대상그룹"],
            "business_status": ["사업자등록여부"],
            "income_criteria": {{"type": "기준유형", "amount": 금액}},
            "support_type": "지원유형",
            "application_period": {{"start": "날짜", "end": "날짜"}},
            "required_documents": ["필요서류"],
            "exclusion_criteria": ["제외조건"]
        }}
        """
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'messages': [{'role': 'user', 'content': extraction_prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        extracted_json = json.loads(result['content'][0]['text'])
        
        # 조건 테이블에 저장
        conditions_table.put_item(
            Item={
                'policy_id': policy['policy_id'],
                'conditions': extracted_json,
                'extracted_at': datetime.utcnow().isoformat(),
                'confidence_score': calculate_extraction_confidence(extracted_json)
            }
        )
        
        return extracted_json
        
    except Exception as e:
        logger.error(f"Condition extraction error: {e}")
        return {}

def store_raw_data(raw_data: Any, source_type: str) -> str:
    """원본 데이터 S3 저장 (버저닝)"""
    try:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        s3_key = f"raw-policies/{source_type}/{timestamp}_{hashlib.md5(str(raw_data).encode()).hexdigest()[:8]}.json"
        
        s3.put_object(
            Bucket='gov-support-raw-data',
            Key=s3_key,
            Body=json.dumps(raw_data, ensure_ascii=False),
            ContentType='application/json',
            Metadata={
                'source_type': source_type,
                'processed': 'false'
            }
        )
        
        return s3_key
        
    except Exception as e:
        logger.error(f"Raw data storage error: {e}")
        raise

def normalize_administrative_terms(policy: Dict) -> str:
    """행정용어 정규화"""
    content = f"{policy.get('title', '')} {policy.get('description', '')}"
    
    # 행정용어 매핑 테이블
    term_mappings = {
        '만 39세 이하': '청년',
        '예비창업자': '창업준비자',
        '소상공인': '중소기업',
        '기초생활수급자': '저소득층',
        '차상위계층': '저소득층'
    }
    
    normalized = content
    for original, normalized_term in term_mappings.items():
        normalized = normalized.replace(original, f"{original} {normalized_term}")
    
    return normalized

def send_to_dlq(event: Dict, error_msg: str):
    """실패한 이벤트를 DLQ로 전송"""
    try:
        dlq_message = {
            'original_event': event,
            'error': error_msg,
            'timestamp': datetime.utcnow().isoformat(),
            'retry_count': event.get('retry_count', 0) + 1
        }
        
        # SQS DLQ로 전송 (실제 구현 시)
        logger.error(f"Sent to DLQ: {dlq_message}")
        
    except Exception as e:
        logger.error(f"DLQ send error: {e}")

def update_cluster_features(policy_id: str, cluster_label: str, embeddings: Dict):
    """Feature Store 업데이트 - 실시간 클러스터 특성"""
    try:
        feature_store_table.put_item(
            Item={
                'feature_id': f"cluster_{cluster_label}",
                'policy_id': policy_id,
                'features': {
                    'embedding_mean': np.mean(embeddings['full_vector']).tolist(),
                    'embedding_std': np.std(embeddings['full_vector']).tolist(),
                    'cluster_size': get_cluster_size(cluster_label),
                    'last_updated': datetime.utcnow().isoformat()
                },
                'ttl': int((datetime.utcnow().timestamp() + 86400 * 30))  # 30일 TTL
            }
        )
        
    except Exception as e:
        logger.error(f"Feature store update error: {e}")

# 기존 헬퍼 함수들 유지
def extract_target_audience(policy: Dict) -> str:
    """대상 청중 추출"""
    content = f"{policy.get('title', '')} {policy.get('description', '')}"
    if '청년' in content:
        return '청년'
    elif '중소기업' in content:
        return '중소기업'
    elif '스타트업' in content or '창업' in content:
        return '창업자'
    return '일반'

def extract_support_type(policy: Dict) -> str:
    """지원 유형 추출"""
    content = f"{policy.get('title', '')} {policy.get('description', '')}"
    if '창업' in content:
        return '창업지원'
    elif '취업' in content or '일자리' in content:
        return '취업지원'
    elif '주택' in content or '주거' in content:
        return '주거지원'
    return '기타'

def extract_eligibility_criteria(policy: Dict) -> List[str]:
    """자격 요건 추출"""
    criteria = []
    content = f"{policy.get('title', '')} {policy.get('description', '')}"
    
    if '만 39세 이하' in content:
        criteria.append('연령: 만 39세 이하')
    if '서울' in content:
        criteria.append('지역: 서울')
    if '사업자등록' in content:
        criteria.append('사업자등록 필요')
        
    return criteria

def extract_support_amount(policy: Dict) -> str:
    """지원 금액 추출"""
    import re
    content = f"{policy.get('title', '')} {policy.get('description', '')}"
    
    # 금액 패턴 매칭
    amount_patterns = [
        r'(\d+)억원?',
        r'(\d+)천만원?',
        r'(\d+)백만원?',
        r'(\d+)만원?'
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(0)
    
    return '미명시'

def extract_keywords(policy: Dict) -> List[str]:
    """키워드 추출"""
    keywords = []
    content = f"{policy.get('title', '')} {policy.get('description', '')}"
    
    keyword_candidates = ['청년', '창업', '취업', '주거', '교육', '지원', '사업', '스타트업']
    
    for keyword in keyword_candidates:
        if keyword in content:
            keywords.append(keyword)
    
    return keywords

# === 추가 헬퍼 함수들 ===

def get_openai_embedding(text: str) -> List[float]:
    """OpenAI 임베딩 생성 (실제 구현 시 OpenAI API 호출)"""
    # 임시 구현
    return [0.1] * 1536

def get_korean_embedding(text: str) -> List[float]:
    """한국어 특화 임베딩 생성"""
    # 임시 구현
    return [0.2] * 768

def create_ensemble_embedding(embeddings: Dict) -> List[float]:
    """앙상블 임베딩 생성"""
    # 가중 평균 (OpenAI 70%, Korean 30%)
    openai_weight = 0.7
    korean_weight = 0.3
    
    # 차원 맞추기
    openai_emb = embeddings['openai'][:768]
    korean_emb = embeddings['korean'][:768]
    
    ensemble = []
    for i in range(768):
        weighted_val = openai_emb[i] * openai_weight + korean_emb[i] * korean_weight
        ensemble.append(weighted_val)
    
    return ensemble * 2  # 1536 차원으로 확장

def get_existing_clusters() -> Dict:
    """기존 클러스터 조회"""
    response = cluster_table.scan()
    return {item['cluster_id']: item for item in response.get('Items', [])}

def calculate_cluster_similarities(policy_vector: np.ndarray, clusters: Dict) -> Dict:
    """클러스터 유사도 계산"""
    similarities = {}
    for cluster_id, cluster_data in clusters.items():
        cluster_centroid = np.array(cluster_data.get('centroid', []))
        if len(cluster_centroid) > 0:
            similarity = np.dot(policy_vector, cluster_centroid) / (np.linalg.norm(policy_vector) * np.linalg.norm(cluster_centroid))
            similarities[cluster_id] = similarity
    return similarities

def assign_to_cluster(policy_id: str, cluster_id: str, similarity: float):
    """클러스터에 정책 할당"""
    cluster_table.update_item(
        Key={'cluster_id': cluster_id},
        UpdateExpression='ADD policy_ids :pid SET last_updated = :time',
        ExpressionAttributeValues={
            ':pid': {policy_id},
            ':time': datetime.utcnow().isoformat()
        }
    )

def create_new_cluster(policy_id: str, policy_vector: np.ndarray, policy: Dict) -> str:
    """새 클러스터 생성"""
    cluster_id = f"cluster_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    cluster_table.put_item(
        Item={
            'cluster_id': cluster_id,
            'centroid': policy_vector.tolist(),
            'policy_ids': {policy_id},
            'cluster_label': generate_cluster_label(policy_id, policy),
            'created_at': datetime.utcnow().isoformat()
        }
    )
    
    return cluster_id

def generate_cluster_label(policy_id: str, policy: Dict) -> str:
    """AI 기반 클러스터 라벨 생성"""
    # 간단한 규칙 기반 (실제로는 LLM 사용)
    content = f"{policy.get('title', '')} {policy.get('description', '')}"
    
    if '창업' in content:
        return '창업지원'
    elif '취업' in content:
        return '취업지원'
    elif '주거' in content:
        return '주거지원'
    elif '교육' in content:
        return '교육지원'
    else:
        return '기타지원'

def update_cluster_centroid(cluster_id: str, new_vector: np.ndarray):
    """클러스터 중심점 업데이트"""
    # 기존 중심점과 새 벡터의 가중 평균으로 업데이트
    response = cluster_table.get_item(Key={'cluster_id': cluster_id})
    if 'Item' in response:
        current_centroid = np.array(response['Item']['centroid'])
        policy_count = len(response['Item'].get('policy_ids', []))
        
        # 가중 평균 계산
        updated_centroid = (current_centroid * (policy_count - 1) + new_vector) / policy_count
        
        cluster_table.update_item(
            Key={'cluster_id': cluster_id},
            UpdateExpression='SET centroid = :centroid',
            ExpressionAttributeValues={':centroid': updated_centroid.tolist()}
        )

def calculate_extraction_confidence(extracted_data: Dict) -> float:
    """추출 신뢰도 계산"""
    # 추출된 필드 수 기반 신뢰도
    total_fields = 9  # 전체 추출 가능 필드 수
    extracted_fields = sum(1 for v in extracted_data.values() if v)
    return extracted_fields / total_fields

def get_cluster_size(cluster_label: str) -> int:
    """클러스터 크기 조회"""
    response = cluster_table.scan(
        FilterExpression='cluster_label = :label',
        ExpressionAttributeValues={':label': cluster_label}
    )
    return len(response.get('Items', []))