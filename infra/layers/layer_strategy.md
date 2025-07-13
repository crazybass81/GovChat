# Lambda Layer 분할 전략

## 현재 문제점
- 모든 Lambda가 동일한 의존성을 개별적으로 포함 (중복)
- 배포 패키지 크기 증가 (Cold Start 지연)
- 의존성 업데이트 시 모든 Lambda 재배포 필요

## 제안하는 레이어 구조 (4개)

### 1. AWS Core Layer (aws-core-layer)
**크기 예상**: ~15MB
**포함 패키지**:
- boto3==1.35.0
- botocore==1.35.99
- s3transfer==0.10.4
- urllib3==1.26.20
- certifi==2025.7.9
- charset-normalizer==3.4.2
- idna==3.10

**사용 Lambda**: 모든 Lambda

### 2. Powertools Layer (powertools-layer)
**크기 예상**: ~8MB
**포함 패키지**:
- aws-lambda-powertools[all]==3.0.0
- aws-xray-sdk==2.14.0
- wrapt==1.17.2

**사용 Lambda**: 모든 Lambda (관측성/로깅)

### 3. Data Processing Layer (data-layer)
**크기 예상**: ~12MB
**포함 패키지**:
- pydantic==2.11.7
- pydantic-core==2.33.2
- jsonschema==4.23.0
- jsonschema-specifications==2025.4.1
- referencing==0.36.2
- rpds-py==0.26.0
- fastjsonschema==2.21.1
- annotated-types==0.7.0
- typing-extensions==4.14.1

**사용 Lambda**: chatbot, extract, match, user_profile

### 4. Search & Security Layer (search-security-layer)
**크기 예상**: ~10MB
**포함 패키지**:
- opensearch-py==2.6.0
- requests==2.32.3
- requests-aws4auth==1.3.1
- PyJWT==2.9.0
- cryptography==45.0.5
- cffi==1.17.1
- pycparser==2.22
- jsonpath-ng==1.7.0
- jmespath==1.0.1

**사용 Lambda**: search, chatbot, admin_auth, user_auth

## 레이어별 Lambda 매핑

| Lambda | AWS Core | Powertools | Data | Search & Security |
|--------|----------|------------|------|-------------------|
| chatbot_handler | ✓ | ✓ | ✓ | ✓ |
| search_handler | ✓ | ✓ | - | ✓ |
| match_handler | ✓ | ✓ | ✓ | - |
| extract_handler | ✓ | ✓ | ✓ | - |
| admin_auth_handler | ✓ | ✓ | - | ✓ |
| user_auth_handler | ✓ | ✓ | - | ✓ |
| policy_handler | ✓ | ✓ | ✓ | - |
| user_profile_handler | ✓ | ✓ | ✓ | - |

## 예상 효과
- **배포 크기 감소**: 개별 Lambda 크기 70% 감소
- **Cold Start 개선**: 초기화 시간 30-40% 단축
- **관리 효율성**: 의존성 업데이트 시 레이어만 갱신
- **비용 절감**: 스토리지 및 전송 비용 감소

## 구현 우선순위
1. AWS Core Layer (가장 큰 효과)
2. Powertools Layer (표준화)
3. Data Processing Layer (특화 기능)
4. Search & Security Layer (보안 중요)