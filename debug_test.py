#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "infra", "src"))

class ConversationEngine:
    def __init__(self):
        pass
    
    def extract_user_info(self, message, current_profile):
        extracted = current_profile.copy()
        print(f"Processing message: '{message}'")
        
        if "서울" in message:
            extracted["region"] = "서울"
            print("  -> Found 서울")
        if "20대" in message:
            extracted["age_group"] = "20대"
            print("  -> Found 20대")
        if "30대" in message:
            extracted["age_group"] = "30대"
            print("  -> Found 30대")
        if "사업자등록 안되어있" in message:
            extracted["business_status"] = "아니오"
            print("  -> Found 사업자등록 안되어있")
        elif "사업자등록 되어있" in message:
            extracted["business_status"] = "예"
            print("  -> Found 사업자등록 되어있")
        
        print(f"  -> Result: {extracted}")
        return extracted

# 테스트
engine = ConversationEngine()

test_cases = [
    ("서울에 살고 있어요", {"region": "서울"}),
    ("20대 청년입니다", {"age_group": "20대"}),
    ("사업자등록 되어있어요", {"business_status": "예"}),
    ("사업자등록 안되어있어요", {"business_status": "아니오"}),
]

for message, expected in test_cases:
    print(f"\n=== Testing: {message} ===")
    extracted = engine.extract_user_info(message, {})
    print(f"Expected: {expected}")
    print(f"Got: {extracted}")
    
    for key, value in expected.items():
        actual = extracted.get(key)
        if actual == value:
            print(f"✓ {key}: {actual} == {value}")
        else:
            print(f"✗ {key}: {actual} != {value}")