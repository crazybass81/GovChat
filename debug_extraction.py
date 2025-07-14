#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "infra", "src"))

from chatbot.conversation_engine import ConversationEngine

engine = ConversationEngine()

# 테스트 메시지
message = "서울에 살고 있고 30살이며 창업을 준비하고 있습니다"
profile = {}

print(f"입력 메시지: {message}")
print(f"기존 프로필: {profile}")

result = engine.extract_user_info(message, profile)
print(f"추출 결과: {result}")

# 개별 테스트
print("\n=== 개별 패턴 테스트 ===")
print(f"'서울' in message: {'서울' in message}")
print(f"'30살' in message: {'30살' in message}")
print(f"'창업' in message: {'창업' in message}")

# 정규식 테스트
import re
age_match = re.search(r"(\d+)살", message)
print(f"나이 정규식 매치: {age_match.group(1) if age_match else 'None'}")