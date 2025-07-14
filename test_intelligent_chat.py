#!/usr/bin/env python3
"""
지능형 챗봇 테스트
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "infra", "src"))

from functions.chatbot_handler import handler

def test_intelligent_conversation():
    """지능형 대화 테스트"""
    
    print("=== 지능형 챗봇 대화 테스트 ===\n")
    
    # 1. 인사
    event1 = {"body": json.dumps({"message": "안녕하세요", "session_id": "test_123"})}
    response1 = handler(event1, {})
    body1 = json.loads(response1["body"])
    print(f"1. 인사: {body1['message']}")
    print(f"   타입: {body1['type']}\n")
    
    # 2. 동의
    event2 = {"body": json.dumps({
        "message": "동의합니다", 
        "session_id": "test_123",
        "user_profile": {},
        "questions_asked": []
    })}
    response2 = handler(event2, {})
    body2 = json.loads(response2["body"])
    print(f"2. 동의 후: {body2['message']}")
    print(f"   타입: {body2['type']}")
    print(f"   옵션: {body2.get('options', [])}\n")
    
    # 3. 복합 답변 (지역 + 나이 + 창업 의도)
    event3 = {"body": json.dumps({
        "message": "서울에 살고 있고 30살이며 창업을 준비하고 있습니다", 
        "session_id": "test_123",
        "user_profile": body2.get("user_profile", {}),
        "questions_asked": body2.get("questions_asked", [])
    })}
    response3 = handler(event3, {})
    body3 = json.loads(response3["body"])
    print(f"3. 복합 답변 후: {body3['message']}")
    print(f"   타입: {body3['type']}")
    print(f"   프로필: {body3.get('user_profile', {})}")
    
    if body3['type'] == 'result':
        print(f"   추천 결과: {body3.get('recommendations', [])}")
    else:
        print(f"   다음 질문 옵션: {body3.get('options', [])}")

if __name__ == "__main__":
    test_intelligent_conversation()