"""
질문 생성 핸들러
"""

import json
from typing import Any, Dict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """질문 생성 Lambda 핸들러"""
    try:
        # 요청 본문 파싱
        body = json.loads(event.get("body", "{}"))
        user_profile = body.get("userProfile", {})
        policy_text = body.get("policyText", "")

        logger.info(
            "Processing question generation",
            extra={"user_profile": user_profile, "policy_text_length": len(policy_text)},
        )

        # 간단한 질문 생성 로직
        question = generate_question(user_profile, policy_text)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            },
            "body": json.dumps({"question": question}),
        }

    except Exception as e:
        logger.error("Error in question handler", extra={"error": str(e)})
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            },
            "body": json.dumps({"error": "Internal server error"}),
        }


def generate_question(user_profile: Dict[str, Any], policy_text: str) -> str:
    """사용자 프로필과 정책 텍스트를 기반으로 질문 생성"""

    # 기본 질문들
    questions = [
        "연령대를 알려주시면 맞춤 지원사업을 찾을 수 있어요. 몇 년생이신가요?",
        "거주 중인 시·도를 알려주실 수 있나요?",
        "현재 어떤 형태로 일하고 계신가요? (직장인, 예비창업자 등)",
        "사업 분야나 업종을 알려주시면 더 정확한 매칭이 가능해요.",
    ]

    # 사용자 프로필에 따른 질문 선택
    if not user_profile.get("region"):
        return questions[1]
    elif not user_profile.get("age"):
        return questions[0]
    elif not user_profile.get("employment"):
        return questions[2]
    else:
        return questions[3]
