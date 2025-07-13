"""
대화 엔진 - 사용자 조건 추출 및 질문 생성
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from aws_lambda_powertools import Logger

logger = Logger()


@dataclass
class QuestionMetadata:
    """질문 메타데이터"""
    field: str
    question: str
    options: Optional[List[str]] = None
    sensitivity: float = 0.5
    requires_consent: bool = False


class ConversationEngine:
    """대화 엔진 - 조건 추출 및 질문 생성"""
    
    def __init__(self):
        self.question_bank = [
            QuestionMetadata("region", "거주 지역이 어디신가요?", 
                           ["서울", "경기", "인천", "부산", "대구", "기타"]),
            QuestionMetadata("age_group", "연령대를 알려주세요.", 
                           ["20대", "30대", "40대", "50대", "60대 이상"]),
            QuestionMetadata("business_status", "사업자등록이 되어 있나요?", 
                           ["예", "아니오"]),
            QuestionMetadata("income_level", "소득 수준은 어느 정도인가요?", 
                           ["저소득", "중간소득", "고소득"], sensitivity=0.8),
            QuestionMetadata("tax_status", "세금 납부 현황을 알려주세요.", 
                           ["정상", "체납", "면제"], sensitivity=0.9, requires_consent=True),
        ]
    
    def extract_user_info(self, message: str, current_profile: Dict) -> Dict:
        """사용자 메시지에서 정보 추출"""
        extracted = {}
        message_lower = message.lower()
        
        # 지역 추출
        regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산"]
        for region in regions:
            if region in message:
                extracted["region"] = region
                break
        
        # 연령 추출
        if "20대" in message or "이십대" in message:
            extracted["age_group"] = "20대"
        elif "30대" in message or "삼십대" in message:
            extracted["age_group"] = "30대"
        elif "40대" in message or "사십대" in message:
            extracted["age_group"] = "40대"
        
        # 사업자 상태 추출
        if "사업자등록" in message:
            if "되어있" in message or "있어요" in message or "있습니다" in message:
                extracted["business_status"] = "예"
            elif "안되어있" in message or "없어요" in message or "없습니다" in message:
                extracted["business_status"] = "아니오"
        
        return extracted
    
    def get_next_question(self, user_profile: Dict, questions_asked: List[str]) -> Optional[QuestionMetadata]:
        """다음 질문 선택"""
        for question in self.question_bank:
            if (question.field not in user_profile and 
                question.field not in questions_asked):
                return question
        return None
    
    def generate_response(self, user_message: str, session_data: Dict) -> Dict:
        """응답 생성"""
        user_profile = session_data.get("profile", {})
        questions_asked = session_data.get("questions_asked", [])
        
        # 정보 추출
        extracted_info = self.extract_user_info(user_message, user_profile)
        user_profile.update(extracted_info)
        
        # 다음 질문 선택
        next_question = self.get_next_question(user_profile, questions_asked)
        
        if next_question:
            return {
                "type": "question",
                "message": next_question.question,
                "options": next_question.options,
                "field": next_question.field,
                "profile": user_profile
            }
        else:
            return {
                "type": "complete",
                "message": "필요한 정보를 모두 수집했습니다! 맞춤 지원사업을 찾아드리겠습니다.",
                "profile": user_profile
            }