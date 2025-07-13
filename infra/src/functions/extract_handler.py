"""
정책 조건 추출 핸들러
"""

import json
import re
from typing import Any, Dict

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()


@tracer.capture_lambda_handler
@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """정책 조건 추출 Lambda 핸들러"""
    try:
        # 요청 본문 파싱
        body = json.loads(event.get("body", "{}"))
        policy_text = body.get("policyText", "")

        logger.info("Processing policy extraction", extra={"policy_text_length": len(policy_text)})

        # 정책 조건 추출
        conditions = extract_policy_conditions(policy_text)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            },
            "body": json.dumps(conditions),
        }

    except Exception as e:
        logger.error("Error in extract handler", extra={"error": str(e)})
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
            },
            "body": json.dumps({"error": "Internal server error"}),
        }


def extract_policy_conditions(policy_text: str) -> Dict[str, Any]:
    """정책 텍스트에서 조건 추출"""
    conditions = {}

    # 연령 조건 추출
    age_match = re.search(r"만\s?(\d{1,2})세\s?이하", policy_text)
    if age_match:
        conditions["age"] = {"max": int(age_match.group(1)), "unit": "세"}

    # 지역 조건 추출
    if "서울" in policy_text:
        conditions["region"] = "서울"
    elif "경기" in policy_text:
        conditions["region"] = "경기"
    elif "부산" in policy_text:
        conditions["region"] = "부산"

    # 창업 관련 조건
    if "예비창업자" in policy_text or "창업" in policy_text:
        conditions["employment"] = "예비창업자"
    elif "청년" in policy_text:
        conditions["target"] = "청년"

    return conditions
