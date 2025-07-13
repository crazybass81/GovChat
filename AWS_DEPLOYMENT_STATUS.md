# 🚀 GovChat AWS 배포 현황 문서

## 📋 프로젝트 개요

**GovChat**은 정부 재정 지원사업 정보를 수집하고 사용자에게 맞춤 매칭해주는 AI 챗봇 서비스입니다.

**배포 정보**
- AWS 계정: `036284794745`
- 리전: `us-east-1` (버지니아 북부)
- 배포일: 2025-07-12 (최종 업데이트)
- 아키텍처: 서버리스 (Next.js + API Gateway + Lambda + DynamoDB + OpenSearch)

## 🏗️ CloudFormation 스택

### 1. **GovChatStack** (메인 애플리케이션)
- **스택 ID**: `arn:aws:cloudformation:us-east-1:036284794745:stack/GovChatStack/ab69ac50-5ebb-11f0-9a9a-0e3bb289c72b`
- **상태**: `UPDATE_COMPLETE`
- **생성일**: 2025-07-12 01:00:58 UTC
- **최종 업데이트**: 2025-07-12 23:51:20 UTC

**주요 출력값**:
- **API 엔드포인트**: `https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/`
- **OpenSearch 엔드포인트**: `https://2oq13hz69l8klsbt9ejg.us-east-1.aoss.amazonaws.com`
- **알람 토픽**: `arn:aws:sns:us-east-1:036284794745:GovChat-Alarms`

### 2. **GovChatAuthStack** (인증 시스템)
- **상태**: `UPDATE_COMPLETE`
- **생성일**: 2025-07-12 09:25:28 UTC
- **최종 업데이트**: 2025-07-12 11:47:34 UTC

### 3. **GovChat-Network** (네트워크 인프라)
- **상태**: `CREATE_COMPLETE`
- **생성일**: 2025-07-10 21:09:57 UTC

## 🔧 Lambda 함수들

### 메인 애플리케이션 함수들 (Python 3.12)

| 함수명 | 핸들러 | 메모리 | 타임아웃 | 용도 |
|--------|---------|---------|----------|------|
| **ChatbotLambda** | `functions.chatbot_handler.handler` | 512MB | 30초 | 챗봇 대화 처리 |
| **SearchLambda** | `functions.search_handler.handler` | 256MB | 30초 | 정책 검색 |
| **MatchLambda** | `functions.match_handler.handler` | 256MB | 30초 | 정책 매칭 |
| **ExtractLambda** | `functions.extract_handler.handler` | 256MB | 30초 | 데이터 추출 |
| **PolicyLambda** | `functions.policy_handler.handler` | 256MB | 30초 | 정책 관리 |
| **UserAuthLambda** | `functions.user_auth_handler.handler` | 256MB | 30초 | 사용자 인증 |
| **AdminAuthLambda** | `functions.admin_auth_handler.handler` | 256MB | 30초 | 관리자 인증 |
| **UserProfileLambda** | `functions.user_profile_handler.handler` | 256MB | 30초 | 사용자 프로필 |

### 인증 함수 (Node.js 20.x)
- **JwtAuthorizerFunction**: JWT 토큰 검증 (128MB, 30초)

### 공통 환경변수
```bash
API_KEY_SECRET=dev-secret-key
AWS_XRAY_TRACING_NAME=GovChat
KMS_KEY_ID=20a9226e-e658-4623-87a8-2503ce616167
OPENSEARCH_HOST=https://2oq13hz69l8klsbt9ejg.us-east-1.aoss.amazonaws.com
CACHE_TABLE=govchat-cache-v3
DATA_BUCKET=govchat-data-v3-036284794745
PYTHONIOENCODING=UTF-8
```

### 🎯 Lambda 함수별 역할

#### 핵심 비즈니스 로직
- **ChatbotLambda**: AI 챗봇 대화 처리 및 조건 추출
- **SearchLambda**: OpenSearch 기반 정책 검색
- **MatchLambda**: 사용자 조건과 정책 매칭
- **ExtractLambda**: 보도자료/문서에서 정책 정보 자동 추출

#### 데이터 관리
- **PolicyLambda**: 정책 CRUD 및 외부 API 동기화
- **ExternalDataSyncHandler**: 공공데이터 포털 API 연동

#### 사용자 관리
- **UserAuthLambda**: 사용자 인증 (이메일/소셜 로그인)
- **AdminAuthLambda**: 관리자 인증 및 권한 관리
- **UserProfileLambda**: 대화 기반 프로필 자동 완성

## 🗄️ 데이터베이스 (DynamoDB)

| 테이블명 | 용도 |
|----------|------|
| **PoliciesTable** | 정책 데이터 저장 |
| **PolicyVersionTable** | 정책 버전 관리 |
| **UserTable** | 사용자 정보 |
| **UserProfileTable** | 사용자 프로필 |
| **govchat-cache-v3** | 캐시 데이터 |
| **govchat-auth** | 인증 정보 |
| **gov-support-sessions** | 세션 관리 |
| **websocket-connections** | WebSocket 연결 |
| **gov-crawl-progress** | 크롤링 진행상황 |

## 🪣 S3 버킷

| 버킷명 | 용도 |
|--------|------|
| **govchat-data-v3-036284794745** | 메인 데이터 저장소 |
| **gov-api-raw-data-036284794745-us-east-1** | 원본 API 데이터 |
| **gov-api-processed-data-036284794745-us-east-1** | 처리된 데이터 |
| **gov-support-data** | 지원 데이터 |

## 🌐 API Gateway

**GovChat API v3**
- **API ID**: `mda1qa36df`
- **엔드포인트**: `https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/`
- **타입**: Edge-optimized
- **생성일**: 2025-07-12 01:01:15 UTC

### API 엔드포인트 구조
```
https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/
├── /chat      → ChatbotLambda
├── /search    → SearchLambda  
├── /match     → MatchLambda
├── /extract   → ExtractLambda
├── /policies  → PolicyLambda
├── /auth      → UserAuthLambda
├── /admin     → AdminAuthLambda
└── /profile   → UserProfileLambda
```

## 🔍 OpenSearch Serverless ("원서치" 시스템)

**클러스터 엔드포인트**: `https://2oq13hz69l8klsbt9ejg.us-east-1.aoss.amazonaws.com`

### 주요 기능
- **전문 검색**: 정책명, 내용, 대상 등 전체 텍스트 검색
- **벡터 검색**: 의미 기반 유사도 검색 (semantic search)
- **임베딩 저장**: 정책 설명문의 벡터 임베딩 인덱싱
- **클러스터링**: 유사 정책 그룹화 및 카테고리 자동 분류

### 검색 전략
1. **키워드 매칭**: 기본 전문 검색
2. **벡터 유사도**: 표현이 달라도 의미가 비슷한 정책 발견
3. **하이브리드 검색**: 키워드 + 벡터 복합 검색으로 정확도 향상

## 🔐 보안 설정

### KMS 암호화
- **KMS 키 ID**: `20a9226e-e658-4623-87a8-2503ce616167`
- DynamoDB, S3 데이터 암호화

### IAM 역할
- Lambda 함수별 최소권한 원칙 적용
- CloudFormation 실행 역할: `cdk-hnb659fds-cfn-exec-role`

## 📊 모니터링 및 알람

### CloudWatch
- **알람 토픽**: `arn:aws:sns:us-east-1:036284794745:GovChat-Alarms`
- **X-Ray 추적**: 모든 Lambda 함수에 활성화
- **로그 그룹**: 함수별 개별 로그 그룹 설정

### 로그 그룹 예시
```
/aws/lambda/GovChat-ChatbotLambda
/aws/lambda/GovChat-SearchLambda
/aws/lambda/GovChat-MatchLambda
/aws/lambda/GovChat-ExtractLambda
...
```

## 🚀 배포 상태 요약

### ✅ 정상 운영 중
- **메인 스택**: GovChatStack (UPDATE_COMPLETE)
- **인증 스택**: GovChatAuthStack (UPDATE_COMPLETE)
- **네트워크**: GovChat-Network (CREATE_COMPLETE)

### 📈 리소스 현황
- **Lambda 함수**: 8개 (메인) + 1개 (인증) + 기타
- **DynamoDB 테이블**: 9개
- **S3 버킷**: 4개
- **API Gateway**: 1개

## 🔗 외부 접근 URL

### 🌍 공개 엔드포인트
**메인 API**: https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/

### 📱 API 테스트 방법

#### 기본 테스트
```bash
# 헬스체크
curl https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/health

# 챗봇 대화 테스트
curl -X POST https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "창업 지원 사업 찾고 있어요", "session_id": "test123"}'

# 정책 검색 테스트
curl https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/search?q=청년창업

# 매칭 테스트
curl -X POST https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/match \
  -H "Content-Type: application/json" \
  -d '{"userProfile": {"age": 30, "region": "서울"}, "policyText": "만 39세 이하 서울 거주 청년 대상"}'
```

#### 관리자 기능 테스트
```bash
# 관리자 로그인 (초기 계정: archt723@gmail.com / 1q2w3e2w1q!)
curl -X POST https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/admin/auth \
  -H "Content-Type: application/json" \
  -d '{"email": "archt723@gmail.com", "password": "1q2w3e2w1q!"}'

# 정책 수동 동기화
curl -X POST https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/admin/sync-policies \
  -H "Authorization: Bearer <JWT_TOKEN>"

# 보도자료 자동 추출
curl -X POST https://mda1qa36df.execute-api.us-east-1.amazonaws.com/prod/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "정부는 만 39세 이하 청년 창업자를 대상으로 최대 5천만원을 지원하는 새로운 사업을 발표했다..."}'
```

## 🎯 AI 모델 및 기술 스택

### 현재 사용 모델
- **GPT-4 Mini**: 챗봇 대화 및 조건 추출
- **OpenAI Embeddings**: 벡터 임베딩 생성

### 고려 중인 대안 모델
- **GPT-3.5 Turbo (Fine-tuned)**: 도메인 특화 파인튜닝
- **GPT-4 Full**: 복잡한 매칭 로직용
- **KoGPT/HyperCLOVA**: 한국어 특화 모델
- **Llama 2**: 자가 호스팅 오픈소스 모델

### 하이브리드 매칭 전략
1. **OpenSearch 벡터 검색**: 1차 후보 추출
2. **규칙 기반 필터**: 명확한 조건 (연령, 지역 등) 필터링
3. **AI 모델 평가**: 최종 적합성 점수 산출
4. **다중 추천**: 우선순위별 복수 정책 제안

## 🔄 데이터 수집 및 동기화

### 공공데이터 포털 연동
- **API 키**: `0259O7/...==` (Secrets Manager 보관)
- **수집 대상**: 정부 재정지원사업 통합 정보
- **동기화 주기**: 일 1회 자동 + 관리자 수동 실행

### 데이터 처리 파이프라인
1. **외부 API 호출**: 공공데이터 포털에서 정책 정보 수집
2. **스키마 변환**: GovChat 전용 구조로 정규화
3. **중복 제거**: policy_external_id 기반 중복 검출
4. **임베딩 생성**: 정책 설명문 벡터화
5. **OpenSearch 인덱싱**: 검색 최적화

## 📊 관리자 대시보드 기능

### 접근 정보
- **초기 관리자**: archt723@gmail.com / 1q2w3e2w1q!
- **권한**: role='admin' 계정만 접근 가능

### 주요 기능
- ✅ **정책 현황 조회**: 전체 정책 리스트 및 필터링
- ✅ **정책 수동 추가**: 신규 정책 직접 입력
- ✅ **정책 수정/삭제**: 기존 정책 정보 업데이트
- ✅ **API 키 관리**: 공공데이터 API 키 설정
- ✅ **데이터 동기화**: 수동 동기화 실행
- 🚧 **보도자료 추출**: AI 기반 자동 필드 추출 (개발 중)
- ✅ **사용자 관리**: 계정 조회 및 권한 관리

## 📅 개발 현황 및 로드맵

### ✅ 완료된 기능
- 서버리스 인프라 구축 (Lambda, DynamoDB, OpenSearch)
- 사용자 인증 시스템 (이메일/소셜 로그인)
- 기본 챗봇 대화 기능
- 정책 검색 및 매칭 로직
- 관리자 대시보드 기본 기능

### 🚧 진행 중인 작업
- AI 매칭 로직 고도화
- 보도자료 자동 추출 기능
- 사용자 프로필 자동 완성
- 벡터 검색 최적화

### 📋 향후 계획
- 소셜 로그인 확장 (Google, Kakao, Naver)
- 실명 인증 연동 (PASS, KISA)
- 모델 성능 최적화 및 파인튜닝
- 사용자 피드백 기반 추천 알고리즘 개선

## 📅 배포 히스토리

- **2025-07-10**: 네트워크 인프라 구축 (GovChat-Network)
- **2025-07-12**: 메인 애플리케이션 배포 (GovChatStack)
- **2025-07-12**: 인증 시스템 추가 (GovChatAuthStack)
- **2025-07-13**: OpenSearch 벡터 검색 최적화
- **2025-07-13**: 관리자 대시보드 기능 확장

---

**프로젝트**: GovChat - 정부지원사업 맞춤 매칭 챗봇  
**문서 생성일**: 2025-07-13  
**최종 확인일**: 2025-07-13  
**기술 스택**: Next.js + AWS Serverless + OpenAI GPT-4 Mini