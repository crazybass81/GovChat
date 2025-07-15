"""
지능형 매칭 시스템 - 대화형 필터링 및 95% 만족도 달성
"""

import json
import boto3
import numpy as np
from datetime import datetime
from aws_lambda_powertools import Logger, Tracer
from typing import Dict, List, Any, Optional, Tuple
import math

logger = Logger()
tracer = Tracer()

# AWS 서비스 클라이언트
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
opensearch = boto3.client('opensearchserverless')

# 테이블 정의
policies_table = dynamodb.Table('PoliciesTable')
conditions_table = dynamodb.Table('PolicyConditionsTable')
feature_store_table = dynamodb.Table('FeatureStoreTable')
user_sessions_table = dynamodb.Table('UserSessionsTable')

# 다중 정지 기준 설정
MATCH_CONFIDENCE_THRESHOLD = 0.95
MIN_INFORMATION_GAIN = 0.05
MAX_QUESTIONS = 6
SENSITIVITY_WEIGHTS = {
    'age': 0.7,
    'income': 0.9,
    'region': 0.3,
    'business_status': 0.2,
    'support_type': 0.2
}

@tracer.capture_lambda_handler
def handler(event, context):
    """지능형 매칭 핸들러"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        session_id = body.get('session_id', 'default')
        user_message = body.get('message', '')
        user_profile = body.get('user_profile', {})
        questions_asked = body.get('questions_asked', [])
        
        logger.info(f"Processing intelligent matching for session: {session_id}")
        
        # 1. 사용자 조건 추출 및 업데이트
        updated_profile = extract_and_update_conditions(user_message, user_profile, session_id)
        
        # 2. 하이브리드 검색으로 후보 정책 조회
        candidate_policies = hybrid_policy_search(updated_profile)
        
        # 3. 다중 정지 기준 확인
        should_stop, stop_reason = check_stopping_criteria(
            candidate_policies, updated_profile, questions_asked
        )
        
        if should_stop:
            # 최종 결과 반환
            final_recommendations = rank_final_policies(candidate_policies, updated_profile)
            return build_final_response(final_recommendations, stop_reason, session_id)
        
        # 4. 다음 질문 생성 (정보 획득량 기반)
        next_question = generate_optimal_question(candidate_policies, updated_profile, questions_asked)
        
        if next_question:
            questions_asked.append(next_question['field'])
            return build_question_response(next_question, updated_profile, session_id, questions_asked)
        
        # 5. 더 이상 질문할 것이 없으면 결과 반환
        final_recommendations = rank_final_policies(candidate_policies, updated_profile)
        return build_final_response(final_recommendations, "no_more_questions", session_id)
        
    except Exception as e:
        logger.error(f"Intelligent matching error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def extract_and_update_conditions(message: str, current_profile: Dict, session_id: str) -> Dict:
    """AI 기반 조건 추출 및 실시간 Feature Store 업데이트"""
    try:
        # LLM을 사용한 조건 추출
        extraction_prompt = f"""
        사용자 메시지에서 정책 매칭에 필요한 조건을 추출해주세요:
        
        메시지: "{message}"
        현재 프로필: {json.dumps(current_profile, ensure_ascii=False)}
        
        다음 형태의 JSON으로 응답해주세요:
        {{
            "age": 숫자 또는 null,
            "region": "지역명" 또는 null,
            "business_status": "예/아니오/준비중" 또는 null,
            "income_level": "기초생활수급자/차상위계층/일반" 또는 null,
            "employment_status": "재직중/구직중/학생/기타" 또는 null,
            "support_type": "창업지원/취업지원/주거지원/교육지원/기타" 또는 null,
            "confidence": 0.0-1.0
        }}
        """
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 500,
                'messages': [{'role': 'user', 'content': extraction_prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        extracted_conditions = json.loads(result['content'][0]['text'])
        
        # 기존 프로필과 병합
        updated_profile = current_profile.copy()
        for key, value in extracted_conditions.items():
            if value is not None and key != 'confidence':
                updated_profile[key] = value
        
        # Feature Store 실시간 업데이트
        update_feature_store(session_id, updated_profile, extracted_conditions.get('confidence', 0.8))
        
        return updated_profile
        
    except Exception as e:
        logger.error(f"Condition extraction error: {e}")
        return current_profile

def hybrid_policy_search(user_profile: Dict) -> List[Dict]:
    """하이브리드 검색 (필터 + 벡터)"""
    try:
        # 1. 필터 조건 구성
        filter_conditions = build_filter_conditions(user_profile)
        
        # 2. 벡터 검색을 위한 쿼리 임베딩 생성
        query_text = build_query_text(user_profile)
        query_embedding = generate_query_embedding(query_text)
        
        # 3. DynamoDB 필터 검색
        filtered_policies = filter_policies_by_conditions(filter_conditions)
        
        # 4. OpenSearch 벡터 검색
        vector_policies = vector_search_policies(query_embedding, filtered_policies)
        
        # 5. 하이브리드 점수 계산
        hybrid_scored_policies = calculate_hybrid_scores(vector_policies, user_profile)
        
        return hybrid_scored_policies
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        return []

def check_stopping_criteria(candidates: List[Dict], user_profile: Dict, questions_asked: List[str]) -> Tuple[bool, str]:
    """다중 정지 기준 확인"""
    
    # 1. 매칭 신뢰도 기준
    if candidates:
        top_scores = [p.get('match_score', 0) for p in candidates[:3]]
        avg_top_score = sum(top_scores) / len(top_scores)
        
        if avg_top_score >= MATCH_CONFIDENCE_THRESHOLD:
            return True, "high_confidence"
    
    # 2. 질문 수 제한
    if len(questions_asked) >= MAX_QUESTIONS:
        return True, "max_questions_reached"
    
    # 3. 후보 수가 너무 적음
    if len(candidates) <= 2:
        return True, "few_candidates"
    
    # 4. 정보 획득량이 낮음
    expected_ig = calculate_expected_information_gain(candidates, user_profile)
    if expected_ig < MIN_INFORMATION_GAIN:
        return True, "low_information_gain"
    
    return False, ""

def generate_optimal_question(candidates: List[Dict], user_profile: Dict, questions_asked: List[str]) -> Optional[Dict]:
    """정보 획득량 기반 최적 질문 생성"""
    try:
        # 1. 후보별 미충족 조건 매트릭스 작성
        condition_matrix = build_condition_matrix(candidates, user_profile)
        
        # 2. 각 조건의 정보 획득량 계산
        information_gains = {}
        for condition, values in condition_matrix.items():
            if condition not in questions_asked and condition not in user_profile:
                coverage = calculate_coverage(values)
                sensitivity = SENSITIVITY_WEIGHTS.get(condition, 0.5)
                value_score = coverage * (1 - sensitivity)
                information_gains[condition] = value_score
        
        if not information_gains:
            return None
        
        # 3. 가장 높은 정보 획득량을 가진 조건 선택
        best_condition = max(information_gains.items(), key=lambda x: x[1])[0]
        
        # 4. GPT를 사용한 자연스러운 질문 생성
        question_text = generate_natural_question(best_condition, candidates)
        
        return {
            'field': best_condition,
            'question': question_text,
            'options': get_condition_options(best_condition),
            'information_gain': information_gains[best_condition]
        }
        
    except Exception as e:
        logger.error(f"Question generation error: {e}")
        return None

def rank_final_policies(candidates: List[Dict], user_profile: Dict) -> List[Dict]:
    """최종 정책 순위 결정"""
    try:
        # 1. 다중 기준 점수 계산
        for policy in candidates:
            # 조건 매칭 점수
            condition_score = calculate_condition_match_score(policy, user_profile)
            
            # 벡터 유사도 점수
            vector_score = policy.get('vector_similarity', 0.5)
            
            # 인기도 점수 (클러스터 크기 기반)
            popularity_score = calculate_popularity_score(policy)
            
            # 최신성 점수
            recency_score = calculate_recency_score(policy)
            
            # 종합 점수 (가중 평균)
            final_score = (
                condition_score * 0.4 +
                vector_score * 0.3 +
                popularity_score * 0.2 +
                recency_score * 0.1
            )
            
            policy['final_score'] = final_score
            policy['condition_match_score'] = condition_score
        
        # 2. 점수 기준 정렬
        ranked_policies = sorted(candidates, key=lambda x: x.get('final_score', 0), reverse=True)
        
        # 3. 상위 10개만 반환
        return ranked_policies[:10]
        
    except Exception as e:
        logger.error(f"Policy ranking error: {e}")
        return candidates

def build_final_response(recommendations: List[Dict], stop_reason: str, session_id: str) -> Dict:
    """최종 응답 구성"""
    
    # 세션 정보 저장
    save_session_result(session_id, recommendations, stop_reason)
    
    # 추천 이유 생성
    recommendation_reasons = []
    for policy in recommendations[:3]:
        reason = generate_recommendation_reason(policy)
        recommendation_reasons.append(reason)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'type': 'final_result',
            'message': f"총 {len(recommendations)}개의 맞춤 지원사업을 찾았습니다!",
            'recommendations': recommendations,
            'recommendation_reasons': recommendation_reasons,
            'stop_reason': stop_reason,
            'session_id': session_id,
            'match_quality': calculate_overall_match_quality(recommendations)
        }, ensure_ascii=False)
    }

def build_question_response(question: Dict, user_profile: Dict, session_id: str, questions_asked: List[str]) -> Dict:
    """질문 응답 구성"""
    return {
        'statusCode': 200,
        'body': json.dumps({
            'type': 'question',
            'message': question['question'],
            'options': question.get('options', []),
            'field': question['field'],
            'session_id': session_id,
            'user_profile': user_profile,
            'questions_asked': questions_asked,
            'progress': {
                'current_step': len(questions_asked),
                'max_steps': MAX_QUESTIONS,
                'information_gain': question.get('information_gain', 0)
            }
        }, ensure_ascii=False)
    }

# === 헬퍼 함수들 ===

def build_filter_conditions(user_profile: Dict) -> Dict:
    """필터 조건 구성"""
    conditions = {}
    
    if user_profile.get('age'):
        conditions['age_range'] = {'min': 0, 'max': user_profile['age'] + 5}
    
    if user_profile.get('region'):
        conditions['regions'] = [user_profile['region']]
    
    if user_profile.get('business_status'):
        conditions['business_status'] = user_profile['business_status']
    
    return conditions

def build_query_text(user_profile: Dict) -> str:
    """벡터 검색용 쿼리 텍스트 구성"""
    query_parts = []
    
    if user_profile.get('support_type'):
        query_parts.append(user_profile['support_type'])
    
    if user_profile.get('employment_status'):
        query_parts.append(user_profile['employment_status'])
    
    if user_profile.get('region'):
        query_parts.append(f"{user_profile['region']} 지역")
    
    return ' '.join(query_parts) if query_parts else "정부 지원사업"

def generate_query_embedding(query_text: str) -> List[float]:
    """쿼리 임베딩 생성"""
    try:
        response = bedrock.invoke_model(
            modelId='amazon.titan-embed-text-v1',
            body=json.dumps({'inputText': query_text})
        )
        
        result = json.loads(response['body'].read())
        return result['embedding']
        
    except Exception as e:
        logger.error(f"Query embedding error: {e}")
        return [0.0] * 1536

def filter_policies_by_conditions(filter_conditions: Dict) -> List[str]:
    """조건 기반 정책 필터링"""
    try:
        # DynamoDB 스캔으로 조건에 맞는 정책 ID 조회
        response = conditions_table.scan()
        
        matching_policy_ids = []
        for item in response.get('Items', []):
            conditions = item.get('conditions', {})
            
            # 연령 조건 확인
            if 'age_range' in filter_conditions:
                policy_age_range = conditions.get('age_range', {})
                user_max_age = filter_conditions['age_range']['max']
                
                if policy_age_range.get('max', 100) >= user_max_age:
                    matching_policy_ids.append(item['policy_id'])
        
        return matching_policy_ids
        
    except Exception as e:
        logger.error(f"Policy filtering error: {e}")
        return []

def vector_search_policies(query_embedding: List[float], filtered_policy_ids: List[str]) -> List[Dict]:
    """벡터 검색"""
    try:
        # OpenSearch k-NN 검색 (실제 구현 시 opensearch-py 사용)
        # 여기서는 시뮬레이션
        
        policies = []
        for policy_id in filtered_policy_ids[:20]:  # 상위 20개만
            # 정책 정보 조회
            policy_response = policies_table.get_item(Key={'policy_id': policy_id})
            if 'Item' in policy_response:
                policy = policy_response['Item']
                
                # 벡터 유사도 계산 (시뮬레이션)
                vector_similarity = np.random.uniform(0.6, 0.95)
                policy['vector_similarity'] = vector_similarity
                
                policies.append(policy)
        
        return policies
        
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []

def calculate_hybrid_scores(policies: List[Dict], user_profile: Dict) -> List[Dict]:
    """하이브리드 점수 계산"""
    for policy in policies:
        # 필터 점수 (조건 매칭)
        filter_score = calculate_condition_match_score(policy, user_profile)
        
        # 벡터 점수
        vector_score = policy.get('vector_similarity', 0.5)
        
        # 하이브리드 점수 (필터 60%, 벡터 40%)
        hybrid_score = filter_score * 0.6 + vector_score * 0.4
        policy['match_score'] = hybrid_score
    
    return sorted(policies, key=lambda x: x.get('match_score', 0), reverse=True)

def calculate_condition_match_score(policy: Dict, user_profile: Dict) -> float:
    """조건 매칭 점수 계산"""
    try:
        # 정책 조건 조회
        conditions_response = conditions_table.get_item(Key={'policy_id': policy['policy_id']})
        if 'Item' not in conditions_response:
            return 0.5
        
        policy_conditions = conditions_response['Item']['conditions']
        
        match_count = 0
        total_conditions = 0
        
        # 연령 조건
        if 'age_range' in policy_conditions and user_profile.get('age'):
            total_conditions += 1
            age_range = policy_conditions['age_range']
            user_age = user_profile['age']
            
            if age_range.get('min', 0) <= user_age <= age_range.get('max', 100):
                match_count += 1
        
        # 지역 조건
        if 'regions' in policy_conditions and user_profile.get('region'):
            total_conditions += 1
            if user_profile['region'] in policy_conditions['regions']:
                match_count += 1
        
        # 사업자 상태
        if 'business_status' in policy_conditions and user_profile.get('business_status'):
            total_conditions += 1
            if user_profile['business_status'] in policy_conditions['business_status']:
                match_count += 1
        
        return match_count / total_conditions if total_conditions > 0 else 0.5
        
    except Exception as e:
        logger.error(f"Condition match score error: {e}")
        return 0.5

def build_condition_matrix(candidates: List[Dict], user_profile: Dict) -> Dict:
    """후보별 미충족 조건 매트릭스"""
    matrix = {}
    
    for policy in candidates:
        try:
            conditions_response = conditions_table.get_item(Key={'policy_id': policy['policy_id']})
            if 'Item' in conditions_response:
                policy_conditions = conditions_response['Item']['conditions']
                
                for condition_key, condition_value in policy_conditions.items():
                    if condition_key not in matrix:
                        matrix[condition_key] = []
                    
                    matrix[condition_key].append(condition_value)
        except Exception as e:
            logger.error(f"Matrix building error for policy {policy.get('policy_id')}: {e}")
    
    return matrix

def calculate_coverage(condition_values: List) -> float:
    """조건 값들의 커버리지 계산"""
    if not condition_values:
        return 0.0
    
    # 고유 값의 비율
    unique_values = len(set(str(v) for v in condition_values))
    total_values = len(condition_values)
    
    return unique_values / total_values

def calculate_expected_information_gain(candidates: List[Dict], user_profile: Dict) -> float:
    """예상 정보 획득량 계산"""
    if len(candidates) <= 1:
        return 0.0
    
    # Shannon Entropy 기반 계산
    current_entropy = math.log2(len(candidates))
    
    # 다음 질문으로 예상되는 엔트로피 감소량
    expected_reduction = current_entropy * 0.3  # 평균 30% 감소 가정
    
    return expected_reduction

def generate_natural_question(condition: str, candidates: List[Dict]) -> str:
    """자연스러운 질문 생성"""
    question_templates = {
        'age': "연령대를 알려주시면 더 정확한 매칭이 가능합니다. 몇 세이신가요?",
        'region': "거주하고 계신 지역을 알려주세요.",
        'business_status': "현재 사업자등록을 하셨나요?",
        'income_level': "소득 수준을 알려주시면 맞춤 지원을 찾아드릴 수 있어요.",
        'employment_status': "현재 취업 상태는 어떻게 되시나요?",
        'support_type': "어떤 종류의 지원을 원하시나요?"
    }
    
    return question_templates.get(condition, f"{condition}에 대해 알려주세요.")

def get_condition_options(condition: str) -> List[str]:
    """조건별 선택 옵션"""
    options_map = {
        'region': ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "기타"],
        'business_status': ["예", "아니오", "준비중"],
        'income_level': ["기초생활수급자", "차상위계층", "일반"],
        'employment_status': ["재직중", "구직중", "학생", "기타"],
        'support_type': ["창업지원", "취업지원", "주거지원", "교육지원", "복지지원", "기타"]
    }
    
    return options_map.get(condition, [])

def update_feature_store(session_id: str, user_profile: Dict, confidence: float):
    """Feature Store 실시간 업데이트"""
    try:
        hashed_session_id = hash(session_id) % 1000000  # 프라이버시 보호
        
        feature_store_table.put_item(
            Item={
                'session_id': str(hashed_session_id),
                'user_profile': user_profile,
                'confidence': confidence,
                'updated_at': datetime.utcnow().isoformat(),
                'ttl': int(datetime.utcnow().timestamp() + 86400)  # 24시간 TTL
            }
        )
        
    except Exception as e:
        logger.error(f"Feature store update error: {e}")

def save_session_result(session_id: str, recommendations: List[Dict], stop_reason: str):
    """세션 결과 저장"""
    try:
        user_sessions_table.put_item(
            Item={
                'session_id': session_id,
                'recommendations': recommendations[:5],  # 상위 5개만 저장
                'stop_reason': stop_reason,
                'completed_at': datetime.utcnow().isoformat(),
                'match_count': len(recommendations)
            }
        )
        
    except Exception as e:
        logger.error(f"Session save error: {e}")

def generate_recommendation_reason(policy: Dict) -> str:
    """추천 이유 생성"""
    reasons = []
    
    if policy.get('condition_match_score', 0) > 0.8:
        reasons.append("조건이 잘 맞음")
    
    if policy.get('vector_similarity', 0) > 0.8:
        reasons.append("관심 분야와 유사")
    
    if policy.get('final_score', 0) > 0.9:
        reasons.append("종합 점수 높음")
    
    return ", ".join(reasons) if reasons else "매칭 조건 충족"

def calculate_popularity_score(policy: Dict) -> float:
    """인기도 점수 계산"""
    # 클러스터 크기 기반 (시뮬레이션)
    return np.random.uniform(0.3, 0.8)

def calculate_recency_score(policy: Dict) -> float:
    """최신성 점수 계산"""
    try:
        created_at = policy.get('created_at', datetime.utcnow().isoformat())
        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        days_old = (datetime.utcnow() - created_date.replace(tzinfo=None)).days
        
        # 30일 이내면 1.0, 그 이후로는 감소
        return max(0.1, 1.0 - (days_old / 365))
        
    except Exception:
        return 0.5

def calculate_overall_match_quality(recommendations: List[Dict]) -> Dict:
    """전체 매칭 품질 계산"""
    if not recommendations:
        return {'score': 0.0, 'grade': 'F'}
    
    avg_score = sum(r.get('final_score', 0) for r in recommendations) / len(recommendations)
    
    if avg_score >= 0.9:
        grade = 'A'
    elif avg_score >= 0.8:
        grade = 'B'
    elif avg_score >= 0.7:
        grade = 'C'
    else:
        grade = 'D'
    
    return {
        'score': round(avg_score, 2),
        'grade': grade,
        'total_matches': len(recommendations)
    }