#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "infra", "src"))

# 테스트 파일과 동일한 클래스 정의
class QuestionMetadata:
    def __init__(self, field, question, options=None, sensitivity=0.5, requires_consent=False):
        self.field = field
        self.question = question
        self.options = options or []
        self.sensitivity = sensitivity
        self.requires_consent = requires_consent

class ConversationEngine:
    def __init__(self):
        self.question_bank = [
            QuestionMetadata("region", "거주 지역을 알려주세요", ["서울", "경기", "인천"]),
            QuestionMetadata("age_group", "연령대를 알려주세요", ["20대", "30대", "40대"]),
            QuestionMetadata("tax_status", "세금 상태", [], 0.9, True)
        ]
    
    def extract_user_info(self, message, current_profile):
        extracted = current_profile.copy()
        print(f"Processing: '{message}'")
        
        if "서울" in message:
            extracted["region"] = "서울"
            print("  -> region: 서울")
        if "20대" in message:
            extracted["age_group"] = "20대"
            print("  -> age_group: 20대")
        if "30대" in message:
            extracted["age_group"] = "30대"
            print("  -> age_group: 30대")
        
        # 더 구체적인 문자열을 먼저 체크
        if "사업자등록 안되어있" in message:
            extracted["business_status"] = "아니오"
            print("  -> business_status: 아니오")
        elif "사업자등록 되어있" in message:
            extracted["business_status"] = "예"
            print("  -> business_status: 예")
        
        print(f"  Result: {extracted}")
        return extracted

# 개별 테스트
engine = ConversationEngine()

print("=== Individual Tests ===")
test_cases = [
    ("서울에 살고 있어요", {"region": "서울"}),
    ("20대 청년입니다", {"age_group": "20대"}),
    ("사업자등록 되어있어요", {"business_status": "예"}),
    ("사업자등록 안되어있어요", {"business_status": "아니오"}),
]

for i, (message, expected) in enumerate(test_cases):
    print(f"\n--- Test {i+1} ---")
    extracted = engine.extract_user_info(message, {})
    
    success = True
    for key, value in expected.items():
        actual = extracted.get(key)
        if actual != value:
            print(f"FAIL: {key} expected '{value}' but got '{actual}'")
            success = False
        else:
            print(f"PASS: {key} = '{actual}'")
    
    if not success:
        print(f"FAILED at test case {i+1}: {message}")
        break
    else:
        print("PASSED")