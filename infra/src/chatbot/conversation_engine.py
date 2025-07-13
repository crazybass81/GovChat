"""
대화 엔진 - Slot-Filling + 역방향 질문 유도
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class QuestionMetadata:
    """질문 메타데이터"""

    field: str
    question: str
    options: list[str]
    sensitivity: float
    required: bool = True
    condition: Optional[str] = None
    requires_consent: bool = False

    def __post_init__(self):
        if self.sensitivity >= 0.9:
            self.requires_consent = True


class ConversationEngine:
    """대화 엔진"""

    def __init__(self):
        self.lambda_param = 0.3
        self.question_bank = [
            QuestionMetadata(
                field="region",
                question="거주하시는 지역이 어디인가요?",
                options=[
                    "서울",
                    "경기",
                    "인천",
                    "부산",
                    "대구",
                    "광주",
                    "대전",
                    "울산",
                    "세종",
                    "기타",
                ],
                sensitivity=0.2,
            ),
            QuestionMetadata(
                field="age_group",
                question="나이가 어떻게 되시나요?",
                options=["20대", "30대", "40대", "50대", "60대 이상"],
                sensitivity=0.3,
            ),
            QuestionMetadata(
                field="business_status",
                question="사업자 등록이 되어 있나요?",
                options=["예", "아니오", "준비중"],
                sensitivity=0.4,
            ),
            QuestionMetadata(
                field="business_type",
                question="업종이 무엇인가요?",
                options=["제조업", "서비스업", "농업", "건설업", "IT/소프트웨어", "기타"],
                sensitivity=0.3,
                condition="business_status == '예'",
            ),
            QuestionMetadata(
                field="income_level",
                question="연간 소득 수준은 어느 정도인가요?",
                options=["3천만원 미만", "3천-5천만원", "5천-1억원", "1억원 이상"],
                sensitivity=0.7,
            ),
            QuestionMetadata(
                field="support_purpose",
                question="어떤 목적으로 지원사업을 찾고 계신가요?",
                options=["창업", "사업확장", "기술개발", "인력채용", "시설투자", "기타"],
                sensitivity=0.2,
            ),
            QuestionMetadata(
                field="tax_status",
                question="세금 납부에 문제가 있으신가요?",
                options=["정상", "체납 있음", "잘 모름"],
                sensitivity=0.9,
            ),
        ]

    def extract_user_info(self, message: str, current_profile: dict[str, Any]) -> dict[str, Any]:
        """사용자 발화에서 정보 추출"""
        extracted = {}

        # 지역 추출
        regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종"]
        for region in regions:
            if region in message:
                extracted["region"] = region
                break

        # 연령대 추출
        if any(x in message for x in ["20대", "이십대"]):
            extracted["age_group"] = "20대"
        elif any(x in message for x in ["30대", "삼십대"]):
            extracted["age_group"] = "30대"
        elif any(x in message for x in ["40대", "사십대"]):
            extracted["age_group"] = "40대"
        elif any(x in message for x in ["50대", "오십대"]):
            extracted["age_group"] = "50대"
        elif any(x in message for x in ["60대", "육십대", "60대 이상"]):
            extracted["age_group"] = "60대 이상"

        # 사업자 상태 추출
        if any(x in message for x in ["사업자", "등록", "사업자등록"]):
            if any(x in message for x in ["네", "예", "있어", "됐어", "되어있어"]):
                extracted["business_status"] = "예"
            elif any(x in message for x in ["아니", "없어", "안됐어"]):
                extracted["business_status"] = "아니오"
            elif any(x in message for x in ["준비", "예정"]):
                extracted["business_status"] = "준비중"

        return extracted

    def get_next_question(
        self, user_profile: dict[str, Any], questions_asked: list[str]
    ) -> Optional[QuestionMetadata]:
        """다음 질문 선택"""
        available_questions = []

        for question in self.question_bank:
            if question.field in questions_asked:
                continue
            if question.field in user_profile and user_profile[question.field]:
                continue
            if question.condition and not self._evaluate_condition(
                question.condition, user_profile
            ):
                continue
            available_questions.append(question)

        if not available_questions:
            return None

        # 정보 이득 - 민감도 점수로 최적 질문 선택
        best_question = None
        best_score = -float("inf")

        for question in available_questions:
            info_gain = self._calculate_information_gain(question.field, user_profile)
            sensitivity_penalty = self.lambda_param * question.sensitivity
            score = info_gain - sensitivity_penalty

            if score > best_score:
                best_score = score
                best_question = question

        return best_question

    def _evaluate_condition(self, condition: str, user_profile: dict[str, Any]) -> bool:
        """조건 평가"""
        if "business_status == '예'" in condition:
            return user_profile.get("business_status") == "예"
        return True

    def _calculate_information_gain(self, field: str, user_profile: dict[str, Any]) -> float:
        """정보 이득 계산"""
        field_importance = {
            "region": 0.8,
            "business_status": 0.9,
            "business_type": 0.7,
            "age_group": 0.6,
            "income_level": 0.8,
            "support_purpose": 0.9,
            "tax_status": 0.95,
        }

        base_gain = field_importance.get(field, 0.5)
        filled_fields = len([v for v in user_profile.values() if v])
        total_fields = len(self.question_bank)
        completeness = min(filled_fields / total_fields, 1.0)

        adjusted_gain = base_gain * (1 + (1 - completeness) * 0.5)
        return max(0.0, min(adjusted_gain, 1.0))
