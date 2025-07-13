# 코드베이스 정리 계획

## 🚨 즉시 해결해야 할 문제들

### 1. CDK 빌드 아티팩트 정리
```bash
# CDK 빌드 아티팩트 삭제
rm -rf infra/cdk.out/

# .gitignore에 추가
echo "infra/cdk.out/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
```

### 2. 사용하지 않는 파일 제거
- `infra/src/common/database.py` - PostgreSQL 연결 코드 (미사용)
- `infra/src/common/api_auth.py` - 미사용 인증 모듈
- `infra/src/common/data_api_client.py` - 미사용 API 클라이언트

### 3. 누락된 파일 생성
- `infra/src/chatbot/conversation_engine.py` - 테스트에서 참조하는 파일
- `infra/src/functions/question_handler.py` - 테스트에서 참조하는 파일

## 🔄 일관성 개선

### 1. 통합 에러 처리
```python
# common/error_handler.py
def handle_lambda_error(func):
    def wrapper(event, context):
        try:
            return func(event, context)
        except Exception as e:
            logger.error("Lambda error", extra={"error": str(e)})
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Internal server error'})
            }
    return wrapper
```

### 2. 표준 응답 형식
```python
# common/response_builder.py
def build_success_response(data, status_code=200):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        },
        'body': json.dumps(data)
    }
```

### 3. 통합 로깅 설정
```python
# common/logger_config.py
import logging
from aws_lambda_powertools import Logger

def get_logger(name):
    return Logger(service=name, level="INFO")
```

## 📁 디렉토리 구조 정리

### 현재 구조의 문제점
- `infra/src/` 안에 외부 라이브러리와 소스 코드가 혼재
- 테스트 파일이 여러 위치에 분산

### 제안하는 구조
```
gov-support-chat/
├── src/                    # 애플리케이션 소스 코드
│   ├── handlers/          # Lambda 핸들러들
│   ├── common/           # 공통 유틸리티
│   ├── services/         # 비즈니스 로직
│   └── models/           # 데이터 모델
├── tests/                # 모든 테스트 파일
├── infra/                # CDK 인프라 코드
├── frontend/             # Next.js 프론트엔드
└── docs/                 # 문서
```

## 🧹 정리 스크립트

### cleanup.sh
```bash
#!/bin/bash

echo "🧹 코드베이스 정리 시작..."

# 1. CDK 아티팩트 정리
echo "CDK 빌드 아티팩트 삭제 중..."
rm -rf infra/cdk.out/
rm -rf infra/.cdk/

# 2. Python 캐시 정리
echo "Python 캐시 정리 중..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# 3. Node.js 캐시 정리
echo "Node.js 캐시 정리 중..."
rm -rf frontend/.next/
rm -rf frontend/node_modules/.cache/

# 4. 사용하지 않는 파일 제거
echo "사용하지 않는 파일 제거 중..."
rm -f infra/src/common/database.py
rm -f infra/src/common/api_auth.py
rm -f infra/src/common/data_api_client.py

echo "✅ 정리 완료!"
```

## 📋 우선순위

### 높음 (즉시 실행)
1. CDK 아티팩트 삭제
2. .gitignore 업데이트
3. 사용하지 않는 파일 제거

### 중간 (1주일 내)
1. 누락된 파일 생성
2. 에러 처리 통합
3. 응답 형식 표준화

### 낮음 (점진적 개선)
1. 디렉토리 구조 재정리
2. 테스트 커버리지 개선
3. 문서 업데이트

## 🎯 기대 효과

- **저장소 크기 90% 감소** (CDK 아티팩트 제거)
- **빌드 시간 50% 단축** (불필요한 파일 제거)
- **코드 일관성 향상** (표준화된 패턴 적용)
- **유지보수성 개선** (명확한 구조)