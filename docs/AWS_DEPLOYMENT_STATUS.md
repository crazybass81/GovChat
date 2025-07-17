# 🚀 GovChat AWS 배포 현황 문서

## 📋 프로젝트 개요

**GovChat**은 정부 재정 지원사업 정보를 수집하고 사용자에게 맞춤 매칭해주는 AI 챗봇 서비스입니다.

**배포 정보**
- AWS 계정: `036284794745`
- 리전: `us-east-1` (버지니아 북부)
- 배포일: 2025-07-15 (최종 업데이트)
- 아키텍처: 서버리스 (Next.js + API Gateway + Lambda + DynamoDB + OpenSearch)

## 🏗️ CloudFormation 스택

### 1. **GovChatStack** (메인 애플리케이션)
- **상태**: `UPDATE_COMPLETE`
- **생성일**: 2025-07-13 23:28:45 UTC
- **최종 업데이트**: 2025-07-15 04:46:58 UTC

**주요 출력값**:
- **API 엔드포인트**: `https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/`
- **OpenSearch 엔드포인트**: `https://xv4xqd9c2ttr1a9vl23k.us-east-1.aoss.amazonaws.com`
- **알람 토픽**: `arn:aws:sns:us-east-1:036284794745:GovChat-Alarms`

### 2. **GovChatAuthStack** (인증 시스템)
- **상태**: `CREATE_COMPLETE`
- **생성일**: 2025-07-13 23:25:25 UTC

### 3. **GovChatLayerStack** (Lambda 레이어)
- **상태**: `CREATE_COMPLETE`
- **생성일**: 2025-07-13 23:18:49 UTC
- **레이어 개수**: 4개 (AWS Core, Data, Powertools, Search-Security)

### 4. **GovChat-Network** (네트워크 인프라)
- **상태**: `CREATE_COMPLETE`
- **생성일**: 2025-07-10 21:09:57 UTC

## 🔧 Lambda 함수들

### 메인 애플리케이션 함수들 (Python 3.12)

| 함수명 | 핸들러 | 메모리 | 타임아웃 | 용도 | 상태 |
|--------|---------|---------|----------|------|------|
| **ChatbotLambda** | `functions.chatbot_handler.handler` | 512MB | 30초 | 챗봇 대화 처리 | ✅ |
| **SearchLambda** | `functions.search_handler.handler` | 256MB | 30초 | 정책 검색 | ✅ |
| **MatchLambda** | `functions.match_handler.handler` | 256MB | 30초 | 정책 매칭 | ✅ |
| **ExtractLambda** | `functions.extract_handler.handler` | 256MB | 30초 | 데이터 추출 | ✅ |
| **PolicyLambda** | `functions.policy_handler.handler` | 256MB | 30초 | 정책 관리 | ✅ |
| **UserAuthLambda** | `functions.user_auth_handler.handler` | 256MB | 30초 | 사용자 인증 | ✅ |
| **AdminAuthLambda** | `functions.admin_auth_handler.handler` | 256MB | 30초 | 관리자 인증 | ✅ |
| **UserProfileLambda** | `functions.user_profile_handler.handler` | 256MB | 30초 | 사용자 프로필 | ✅ |
| **ExternalSyncLambda** | `functions.external_data_sync_handler.handler` | 256MB | 30초 | 외부 데이터 동기화 | ✅ |

### 인증 함수 (Node.js 20.x)
- **JwtAuthorizerFunction**: JWT 토큰 검증 (128MB, 30초)

### 유틸리티 함수 (Node.js 22.x)
- **CustomS3AutoDeleteObjectsCustomResource**: S3 자동 정리 (128MB, 30초)

### 공통 환경변수
```bash
API_KEY_SECRET=dev-secret-key
AWS_XRAY_TRACING_NAME=GovChat
KMS_KEY_ID=20a9226e-e658-4623-87a8-2503ce616167
OPENSEARCH_HOST=https://xv4xqd9c2ttr1a9vl23k.us-east-1.aoss.amazonaws.com
CACHE_TABLE=govchat-cache-v3
DATA_BUCKET=govchat-data-v3-036284794745
PYTHONIOENCODING=UTF-8
```

## 🗄️ 데이터베이스 (DynamoDB)

| 테이블명 | 용도 | 상태 |
|----------|------|------|
| **PoliciesTable** | 정책 데이터 저장 | ✅ |
| **PolicyVersionTable** | 정책 버전 관리 | ✅ |
| **UserTable** | 사용자 정보 | ✅ |
| **UserProfileTable** | 사용자 프로필 | ✅ |
| **govchat-cache-v3** | 캐시 데이터 | ✅ |

## 🪣 S3 버킷

| 버킷명 | 용도 | 상태 |
|--------|------|------|
| **govchat-data-v3-036284794745** | 메인 데이터 저장소 | ✅ |

## 🌐 API Gateway

**GovChat API v3**
- **API ID**: `l2iyczn1ge`
- **엔드포인트**: `https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/`
- **타입**: Edge-optimized
- **생성일**: 2025-01-12 01:01:15 UTC

### API 엔드포인트 구조
```
https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/
├── /question  → ChatbotLambda (✅ 정상)
├── /search    → SearchLambda (❌ 오류)
├── /match     → MatchLambda (✅ 정상)
├── /extract   → ExtractLambda (✅ 정상)
├── /policies  → PolicyLambda
├── /auth      → UserAuthLambda
├── /admin     → AdminAuthLambda
└── /profile   → UserProfileLambda
```

## 🔍 OpenSearch Serverless ("원서치" 시스템)

**클러스터 엔드포인트**: `https://xv4xqd9c2ttr1a9vl23k.us-east-1.aoss.amazonaws.com`

### 현재 상태
- ✅ **컬렉션 생성**: 완료
- ⚠️ **인덱싱**: 부분 완성
- ❌ **벡터 검색**: 미완성

### 주요 기능 (계획)
- **전문 검색**: 정책명, 내용, 대상 등 전체 텍스트 검색
- **벡터 검색**: 의미 기반 유사도 검색 (semantic search)
- **임베딩 저장**: 정책 설명문의 벡터 임베딩 인덱싱
- **클러스터링**: 유사 정책 그룹화 및 카테고리 자동 분류

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

## 🚀 배포 상태 요약

### ✅ 정상 운영 중
- **메인 스택**: GovChatStack (UPDATE_COMPLETE)
- **인증 스택**: GovChatAuthStack (UPDATE_COMPLETE)
- **레이어 스택**: GovChatLayerStack (CREATE_COMPLETE)

### 📈 리소스 현황
- **Lambda 함수**: 8개 (메인) + 1개 (인증)
- **DynamoDB 테이블**: 5개
- **S3 버킷**: 1개
- **API Gateway**: 1개
- **OpenSearch 컬렉션**: 1개

## 🧪 헬스체크 결과 (2025-07-15)

| 엔드포인트 | 상태 | 응답시간 | 비고 |
|-----------|------|----------|------|
| /question | ✅ OK | 0.69s | 정상 동작 |
| /search | ✅ OK | 0.046s | 정상 동작 |
| /extract | ✅ OK | 1.12s | 정상 동작 |
| /match | ✅ OK | 0.68s | 정상 동작 |
| /policies | ✅ OK | - | 정상 동작 |
| /auth | ✅ OK | - | 정상 동작 |
| /profile | ✅ OK | - | 정상 동작 |

## 🔗 외부 접근 URL

### 🌍 공개 엔드포인트
**메인 API**: https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/

### 📱 API 테스트 방법

#### 정상 동작 엔드포인트
```bash
# 질문 처리 테스트
curl -X POST https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/question \
  -H "Content-Type: application/json" \
  -d '{"message": "창업 지원 사업 찾고 있어요"}'

# 데이터 추출 테스트
curl -X POST https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "만 39세 이하 청년 창업자 지원사업"}'

# 매칭 테스트
curl -X POST https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/match \
  -H "Content-Type: application/json" \
  -d '{"userProfile": {"age": 30}, "query": "창업지원"}'
```

#### 수정 필요 엔드포인트
```bash
# 검색 (현재 오류)
curl https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/search?q=창업
# ❌ 오류 발생 - 수정 필요
```

## 🎯 다음 작업 우선순위

### 🚨 긴급 (즉시 필요)
1. **환경변수 설정**
   ```bash
   OPENAI_API_KEY=your-openai-api-key
   GOV_API_KEY=0259O7/MNmML1Vc3Q2zGYep/IdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv/dxa+UvOzEtsxCRzA==
   ```

2. **OpenSearch 인덱스 생성**
   - 벡터 매핑 활성화
   - 임베딩 인덱싱 시작

3. **실제 데이터 동기화**
   - K-Startup API 연동
   - 정책 데이터 임베딩 생성

### ⚠️ 중요 (단기 목표)
4. **관리자 대시보드 완성**
5. **사용자 인터페이스 개선**
6. **성능 최적화**

## 📅 배포 히스토리

- **2025-07-10**: 네트워크 인프라 구축 (GovChat-Network)
- **2025-07-13**: Lambda 레이어 배포 (GovChatLayerStack)
- **2025-07-13**: 인증 시스템 배포 (GovChatAuthStack)
- **2025-07-13**: 메인 애플리케이션 배포 (GovChatStack)
- **2025-07-15**: Lambda 함수 업데이트 및 안정화
- **2025-07-15**: 모든 API 엔드포인트 정상화

---

**프로젝트**: GovChat - 정부지원사업 맞춤 매칭 챗봇  
**문서 생성일**: 2025-01-13  
**최종 확인일**: 2025-01-13  
**기술 스택**: Next.js + AWS Serverless + OpenAI GPT-4 Mini