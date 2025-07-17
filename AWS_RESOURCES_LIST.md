# 🏗️ AWS 리소스 현황 목록

## 📊 CloudFormation 스택

| 스택명 | 상태 | 생성일 | 용도 |
|--------|------|--------|------|
| **GovChatStack** | UPDATE_COMPLETE | 2025-07-13 | 메인 애플리케이션 |
| **GovChatAuthStack** | CREATE_COMPLETE | 2025-07-13 | 인증 시스템 |
| **GovChatLayerStack** | CREATE_COMPLETE | 2025-07-13 | Lambda 레이어 |
| **GovChat-Network** | CREATE_COMPLETE | 2025-07-10 | 네트워크 인프라 |

## 🔧 Lambda 함수 (11개)

### Python 3.12 함수들
| 함수명 | 용도 | 메모리 | 상태 |
|--------|------|--------|------|
| **GovChatStack-ChatbotLambda** | 챗봇 대화 처리 | 512MB | ✅ 정상 |
| **GovChatStack-SearchLambda** | 정책 검색 | 256MB | ✅ 정상 |
| **GovChatStack-MatchLambda** | 정책 매칭 | 256MB | ✅ 정상 |
| **GovChatStack-ExtractLambda** | 데이터 추출 | 256MB | ✅ 정상 |
| **GovChatStack-PolicyLambda** | 정책 관리 | 256MB | ✅ 정상 |
| **GovChatStack-UserAuthLambda** | 사용자 인증 | 256MB | ✅ 정상 |
| **GovChatStack-AdminAuthLambda** | 관리자 인증 | 256MB | ✅ 정상 |
| **GovChatStack-UserProfileLambda** | 사용자 프로필 | 256MB | ✅ 정상 |
| **GovChatStack-ExternalSyncLambda** | 외부 데이터 동기화 | 256MB | ✅ 정상 |

### Node.js 함수들
| 함수명 | 용도 | 런타임 | 상태 |
|--------|------|--------|------|
| **GovChatAuthStack-JwtAuthorizerFunction** | JWT 토큰 검증 | Node.js 20.x | ✅ 정상 |
| **GovChatStack-CustomS3AutoDeleteObjects** | S3 자동 정리 | Node.js 22.x | ✅ 정상 |

## 🌐 API Gateway

| 이름 | ID | 엔드포인트 | 생성일 |
|------|----|-----------|---------| 
| **GovChat API v3** | l2iyczn1ge | https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/ | 2025-07-13 |

### API 엔드포인트 구조
```
https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/
├── /question  → ChatbotLambda (✅ 정상)
├── /search    → SearchLambda (✅ 정상)
├── /match     → MatchLambda (✅ 정상)
├── /extract   → ExtractLambda (✅ 정상)
├── /policies  → PolicyLambda (✅ 정상)
├── /auth      → UserAuthLambda (✅ 정상)
├── /admin     → AdminAuthLambda (✅ 정상)
└── /profile   → UserProfileLambda (✅ 정상)
```

## 🗄️ DynamoDB 테이블 (5개)

| 테이블명 | 용도 | 상태 |
|----------|------|------|
| **PoliciesTable** | 정책 데이터 저장 | ✅ 운영 중 |
| **UserTable** | 사용자 정보 | ✅ 운영 중 |
| **UserProfileTable** | 사용자 프로필 | ✅ 운영 중 |
| **govchat-cache-v3** | 캐시 데이터 | ✅ 운영 중 |
| **govchat-auth** | 인증 데이터 | ✅ 운영 중 |

## 🔍 OpenSearch Serverless

| 구성요소 | 값 | 상태 |
|----------|----|----- |
| **컬렉션 엔드포인트** | https://xv4xqd9c2ttr1a9vl23k.us-east-1.aoss.amazonaws.com | ✅ 운영 중 |
| **용도** | 벡터 검색 및 정책 인덱싱 | ⚠️ 인덱스 생성 필요 |

## 🪣 S3 버킷

| 버킷명 | 용도 | 상태 |
|--------|------|------|
| **govchat-data-v3-036284794745** | 메인 데이터 저장소 | ✅ 운영 중 |

## 🔐 보안 리소스

### KMS 키
- **키 ID**: 20a9226e-e658-4623-87a8-2503ce616167
- **용도**: DynamoDB, S3 데이터 암호화

### IAM 역할
- Lambda 함수별 최소권한 원칙 적용
- CloudFormation 실행 역할: `cdk-hnb659fds-cfn-exec-role`

## 📊 모니터링 리소스

### CloudWatch
- **알람 토픽**: `arn:aws:sns:us-east-1:036284794745:GovChat-Alarms`
- **X-Ray 추적**: 모든 Lambda 함수에 활성화
- **로그 그룹**: 함수별 개별 로그 그룹 설정

## 💰 비용 최적화 설정

### 서버리스 아키텍처
- **Lambda**: 사용량 기반 과금
- **DynamoDB**: On-Demand 모드
- **API Gateway**: 요청 기반 과금
- **OpenSearch**: Serverless 모드

### 리소스 효율성
- **Lambda 레이어**: 공통 라이브러리 최적화
- **메모리 최적화**: 함수별 맞춤 메모리 할당
- **타임아웃 설정**: 적정 타임아웃으로 비용 절약

## 🎯 다음 작업 필요 리소스

### 환경변수 설정 필요
```bash
# Lambda 환경변수 추가 필요
OPENAI_API_KEY=your-openai-api-key
GOV_API_KEY=0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA==
```

### OpenSearch 인덱스 생성 필요
- 벡터 매핑 설정 (1536차원)
- HNSW 알고리즘 설정
- 코사인 유사도 거리 측정

---

**AWS 계정**: 036284794745  
**리전**: us-east-1 (버지니아 북부)  
**총 리소스**: 스택 4개, Lambda 11개, 테이블 5개  
**상태**: 모든 리소스 정상 운영 중 ✅  
**최종 확인일**: 2025-07-15