"""
대화 엔진 - AI 기반 조건 추출 및 동적 질문 생성
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from aws_lambda_powertools import Logger

logger = Logger()

@dataclass
class QuestionMetadata:
    """질문 메타데이터"""
    field: str
    question: str
    options: List[str] = None
    sensitivity: float = 0.5  # 0-1, 높을수록 민감
    requires_consent: bool = False
    filter_power: float = 0.7  # 필터링 기여도

class ConversationEngine:
    """대화 엔진 - 조건 추출 및 질문 생성"""
    
    def __init__(self):
        self.question_bank = [
            QuestionMetadata("region", "거주 중인 시·도를 알려주세요", 
                           ["서울", "경기", "인천", "부산", "대구", "기타"], 0.3, False, 0.8),
            QuestionMetadata("age_group", "연령대를 알려주세요", 
                           ["20대", "30대", "40대", "50대", "60대 이상"], 0.4, False, 0.9),
            QuestionMetadata("business_status", "사업자등록이 되어 있나요?", 
                           ["예", "아니오", "준비중"], 0.2, False, 0.8),
            QuestionMetadata("income_level", "소득 수준을 알려주세요", 
                           ["기초생활수급자", "차상위계층", "일반"], 0.8, True, 0.7),
            QuestionMetadata("employment_status", "현재 취업 상태는?", 
                           ["재직중", "구직중", "학생", "기타"], 0.3, False, 0.6),
            QuestionMetadata("support_type", "어떤 지원을 원하시나요?", 
                           ["창업지원", "취업지원", "주거지원", "교육지원", "기타"], 0.2, False, 0.9)
        ]
    
    def extract_user_info(self, message: str, current_profile: Dict) -> Dict:
        """사용자 메시지에서 조건 추출"""
        extracted = current_profile.copy()
        message_lower = message.lower()
        
        # 지역 추출
        regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종"]
        for region in regions:
            if region in message:
                extracted["region"] = region
                break
        
        # 연령 추출
        age_patterns = [
            (r"(\d+)대", lambda m: f"{m.group(1)}대"),
            (r"(\d+)살", lambda m: self._age_to_group(int(m.group(1)))),
            (r"만\s*(\d+)", lambda m: self._age_to_group(int(m.group(1))))
        ]
        
        for pattern, converter in age_patterns:
            match = re.search(pattern, message)
            if match:
                extracted["age_group"] = converter(match)
                break
        
        # 사업자 상태
        if any(word in message_lower for word in ["사업자", "창업", "사업"]):
            if any(word in message_lower for word in ["없", "안", "아니"]):
                extracted["business_status"] = "아니오"
            else:
                extracted["business_status"] = "예"
        
        # 지원 유형 추출
        support_keywords = {
            "창업지원": ["창업", "사업", "스타트업"],
            "취업지원": ["취업", "일자리", "구직"],
            "주거지원": ["주택", "주거", "임대", "전세"],
            "교육지원": ["교육", "학습", "연수", "교육비"]
        }
        
        for support_type, keywords in support_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                extracted["support_type"] = support_type
                break
        
        return extracted
    
    def get_next_question(self, user_profile: Dict, questions_asked: List[str]) -> Optional[QuestionMetadata]:
        """다음 질문 선택 - AI 기반 동적 선택"""
        
        # 아직 묻지 않은 질문들
        available_questions = [
            q for q in self.question_bank 
            if q.field not in questions_asked and q.field not in user_profile
        ]
        
        if not available_questions:
            return None
        
        # 민감도와 필터링 기여도를 고려한 점수 계산
        scored_questions = []
        for q in available_questions:
            # 기본 점수는 필터링 기여도
            score = q.filter_power
            
            # 민감한 질문은 나중에 (점수 감소)
            if q.requires_consent:
                score *= 0.3
            elif q.sensitivity > 0.6:
                score *= 0.7
            
            # 이미 수집된 정보와 연관성 고려
            if self._is_relevant_question(q, user_profile):
                score *= 1.2
            
            scored_questions.append((score, q))
        
        # 가장 높은 점수의 질문 선택
        scored_questions.sort(key=lambda x: x[0], reverse=True)
        return scored_questions[0][1]
    
    def _age_to_group(self, age: int) -> str:
        """나이를 연령대로 변환"""
        if age < 30:
            return "20대"
        elif age < 40:
            return "30대"
        elif age < 50:
            return "40대"
        elif age < 60:
            return "50대"
        else:
            return "60대 이상"
    
    def _is_relevant_question(self, question: QuestionMetadata, profile: Dict) -> bool:
        """현재 프로필과 질문의 연관성 판단"""
        # 창업 관련 답변이 있으면 사업자 상태 질문이 중요
        if question.field == "business_status" and profile.get("support_type") == "창업지원":
            return True
        
        # 취업 관련이면 고용 상태 질문이 중요
        if question.field == "employment_status" and profile.get("support_type") == "취업지원":
            return True
        
        return False
    
    def should_end_conversation(self, user_profile: Dict, questions_asked: List[str]) -> bool:
        """대화 종료 조건 판단"""
        # 필수 정보가 모두 수집되었는지 확인
        essential_fields = ["region", "age_group", "support_type"]
        
        collected_essential = sum(1 for field in essential_fields if field in user_profile)
        
        # 필수 정보 80% 이상 수집되면 종료 고려
        if collected_essential >= len(essential_fields) * 0.8:
            return True
        
        # 너무 많은 질문을 했으면 종료
        if len(questions_asked) >= 5:
            return True
        
        return False