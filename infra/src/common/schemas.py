"""
공통 데이터 스키마 정의
"""

from typing import Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """사용자 프로필 스키마"""

    model_config = {"extra": "allow", "validate_assignment": True}

    # 기본 정보
    region: Optional[str] = Field(default=None, description="거주 지역")
    age_group: Optional[str] = Field(default=None, description="연령대")
    age: Optional[int] = Field(default=None, description="나이")

    # 사업 정보
    business_status: Optional[str] = Field(default=None, description="사업자 등록 상태")
    business_type: Optional[str] = Field(default=None, description="업종")
    employment: Optional[str] = Field(default=None, description="고용 상태")

    # 경제 정보
    income_level: Optional[str] = Field(default=None, description="소득 수준")
    income: Optional[dict] = Field(default=None, description="소득 정보")

    # 지원 목적
    support_purpose: Optional[str] = Field(default=None, description="지원 목적")

    # 민감 정보
    tax_status: Optional[str] = Field(default=None, description="세금 납부 상태")
    marital_status: Optional[str] = Field(default=None, description="결혼 상태")

    def get_completion_score(self) -> float:
        """프로필 완성도 계산"""
        required_fields = ["region", "business_status", "support_purpose"]
        filled = sum(1 for field in required_fields if getattr(self, field))
        return filled / len(required_fields)


class ConversationResponse(BaseModel):
    """대화 응답 스키마"""

    message: str = Field(..., description="응답 메시지")
    type: str = Field(..., description="메시지 타입")
    session_id: str = Field(..., description="세션 ID")
    options: Optional[list[str]] = Field(None, description="선택 옵션")
    completeness: Optional[float] = Field(None, description="완성도")
    requires_consent: Optional[bool] = Field(None, description="동의 필요")


class SessionData(BaseModel):
    """세션 데이터 스키마"""

    session_id: str
    step: str = "greeting"
    user_profile: dict = Field(default_factory=dict)
    questions_asked: list[str] = Field(default_factory=list)
    consent_given: bool = False
    user_intent: Optional[str] = None
