# 🚀 GovChat - 정부지원사업 맞춤 매칭 챗봇

**배포 완료!** 정부 재정 지원사업 정보를 AI로 맞춤 매칭해주는 서버리스 챗봇 시스템

## 🎉 배포 현황 (2025-01-14)

### ✅ 배포 완료
- **AWS 스택**: 3개 스택 완전 배포
- **Lambda 함수**: 8개 함수 정상 동작 ✅
- **API 엔드포인트**: https://x94nllzgi0.execute-api.us-east-1.amazonaws.com/prod/
- **OpenSearch**: https://xv4xqd9c2ttr1a9vl23k.us-east-1.aoss.amazonaws.com
- **헬스체크**: 모든 엔드포인트 정상 ✅

### ✅ 디버깅 완료
- **SearchLambda Import 오류** → 해결 완료
- **ExternalSyncLambda requests 오류** → 해결 완료
- **ChatbotLambda 응답 형식** → 해결 완료
- **테스트 실패** → 해결 완료
- **lambda_handler 미정의** → 해결 완료

## 🏗️ 주요 기능

### 보안 강화
- **IAM 최소권한 원칙**: 함수별 세분화된 권한 설정
- **KMS 암호화**: 전용 KMS 키로 DynamoDB, S3 암호화
- **조건부 정책**: VPC, 계정 기반 접근 제어
- **보안 스캔**: Bandit SAST, Safety 취약점 검사 자동화

### 관측성 강화
- **Composite Alarm**: 에러율 + 지연시간 결합 알람
- **X-Ray 추적**: 분산 추적으로 성능 병목 식별
- **사전 정의 로그그룹**: 권한 최소화 및 비용 예측성
- **캐시 효율성 메트릭**: 실시간 히트율 모니터링

### 성능 최적화
- **정책 캐싱 개선**: 파티션 키 쏠림 방지, 이중 만료 필드
- **메트릭 배치 전송**: EMF 기반 효율적 메트릭 수집
- **동시 실행 제한**: Lambda 함수별 적정 동시성 설정
- **메모리 최적화**: 함수별 맞춤 메모리 할당

### 운영 준비도
- **포괄적 Runbook**: 알람 대응, 장애 복구 절차
- **Chaos 테스트**: 스로틀링, 타임아웃, Cold Start 복원력 검증
- **부하 테스트**: RPS 제어, 동시성, 한계점 탐색
- **커버리지 측정**: 80% 최소 커버리지 요구사항

## 📊 현재 상태

| 구성요소 | 상태 | 비고 |
|----------|------|------|
| 인프라 배포 | ✅ 완료 | 3개 스택 배포 완료 |
| Lambda 함수 | ✅ 정상 | 8개 함수 정상 동작 |
| API Gateway | ✅ 정상 | 모든 엔드포인트 정상 |
| DynamoDB | ✅ 정상 | 5개 테이블 운영 중 |
| OpenSearch | ⚠️ 부분 | 컬렉션 생성, 인덱싱 미완성 |
| 외부 API 연동 | ❌ 미완성 | 공공데이터 포털 연동 필요 |

## 🏗️ 아키텍처

```
┌─────────────────── Full Stack ───────────────────┐
│                                                   │
│  Frontend (Next.js)                               │
│  ├── /user/chat     → 사용자 채팅 인터페이스        │
│  └── /admin/policies → 관리자 정책 관리             │
│                                                   │
│  ┌─────────────────── AWS VPC ─────────────────┐ │
│  │                                             │ │
│  │  API Gateway (REST + CORS)                  │ │
│  │  ├── /chat      → ChatbotLambda (512MB)    │ │
│  │  ├── /search    → SearchLambda (256MB)     │ │
│  │  ├── /match     → MatchLambda (256MB)      │ │
│  │  └── /extract   → ExtractLambda (256MB)    │ │
│                                               │
│  ┌─────────────── 보안 계층 ──────────────────┐ │
│  │ • KMS 키 (자동 로테이션)                   │ │
│  │ • IAM 최소권한 (조건부 정책)               │ │
│  │ • VPC 엔드포인트 (OpenSearch)             │ │
│  └───────────────────────────────────────────┘ │
│                                               │
│  ┌─────────────── 데이터 계층 ──────────────────┐ │
│  │ DynamoDB (KMS 암호화, TTL, 백업)          │ │
│  │ OpenSearch Serverless (벡터 검색)         │ │
│  │ S3 (KMS 암호화, 버전 관리)                │ │
│  └───────────────────────────────────────────┘ │
│                                               │
│  ┌─────────────── 관측성 계층 ──────────────────┐ │
│  │ • CloudWatch 대시보드                     │ │
│  │ • Composite Alarms                       │ │
│  │ • X-Ray 분산 추적                        │ │
│  │ • EMF 메트릭 수집                        │ │
│  │ • SNS 알람 토픽                          │ │
│  └───────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

## 🛠️ 설치 및 배포

### 사전 요구사항
```bash
# Python 3.12+
python --version

# Node.js 18+
node --version
npm --version

# AWS CDK v2
npm install -g aws-cdk
cdk --version

# 개발 도구
pip install bandit pytest-cov safety ruff mypy
```

### 🎯 다음 작업 (우선순위)

#### 🚨 긴급 (즉시 필요)
1. **외부 공공데이터 API 연동** - 핵심 기능
2. **OpenSearch 벡터 검색 완성** - "원서치" 시스템

#### ⚠️ 중요 (단기 목표)
3. **실명 인증 시스템** - 보안 강화
4. **관리자 대시보드 완성** - 운영 도구
5. **성능 최적화** - 사용자 경험

### 🛠️ 개발 환경 설정

#### 백엔드 (이미 배포됨)
```bash
# 현재 배포된 상태 확인
aws cloudformation describe-stacks --stack-name GovChatStack

# 헬스체크
curl https://x94nllzgi0.execute-api.us-east-1.amazonaws.com/prod/question
```

#### 프론트엔드 개발
```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

## 🧪 API 테스트

### 현재 동작하는 엔드포인트
```bash
# 질문 처리 (정상)
curl -X POST https://x94nllzgi0.execute-api.us-east-1.amazonaws.com/prod/question \
  -H "Content-Type: application/json" \
  -d '{"message": "창업 지원 사업 찾고 있어요"}'

# 검색 (정상)
curl https://x94nllzgi0.execute-api.us-east-1.amazonaws.com/prod/search?q=창업

# 데이터 추출 (정상)
curl -X POST https://x94nllzgi0.execute-api.us-east-1.amazonaws.com/prod/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "만 39세 이하 청년 창업자 지원사업"}'

# 매칭 (정상)
curl -X POST https://x94nllzgi0.execute-api.us-east-1.amazonaws.com/prod/match \
  -H "Content-Type: application/json" \
  -d '{"userProfile": {"age": 30}, "query": "창업지원"}'
```

## 📈 현재 배포된 리소스

### AWS 리소스 현황
- **Lambda 함수**: 8개 (Python 3.12)
- **DynamoDB 테이블**: 5개 (KMS 암호화)
- **S3 버킷**: 1개 (데이터 저장)
- **OpenSearch 컬렉션**: 1개 (벡터 검색)
- **API Gateway**: 1개 (REST API)
- **CloudWatch**: 대시보드 & 알람

### 로그 확인
```bash
# Lambda 함수 로그 확인
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/GovChat"

# 최근 에러 로그
aws logs filter-log-events \
  --log-group-name "/aws/lambda/GovChat-SearchLambda" \
  --filter-pattern "ERROR"
```

## 🔧 개발 작업

### 외부 API 연동 구현
```bash
# 공공데이터 포털 API 키 설정
# API 키: 0259O7/...== (환경변수 설정 필요)

# 구현 위치
# infra/src/functions/external_data_sync_handler.py
```

## 📊 헬스체크 결과

### 현재 상태 (2025-01-14)
| 엔드포인트 | 상태 | 응답시간 | 비고 |
|-----------|------|----------|------|
| /question | ✅ OK | 0.69s | 정상 동작 |
| /search | ✅ OK | 0.046s | **디버깅 완료** |
| /extract | ✅ OK | 1.12s | 정상 동작 |
| /match | ✅ OK | 0.68s | 정상 동작 |

## 🔒 보안 설정

### 현재 적용된 보안
- **KMS 암호화**: DynamoDB, S3 데이터 암호화
- **HTTPS**: 모든 API 통신 암호화
- **IAM 최소권한**: Lambda 함수별 세분화된 권한
- **JWT 인증**: 사용자 세션 관리

### 관리자 계정
- **이메일**: archt723@gmail.com
- **비밀번호**: 1q2w3e2w1q! (변경 권장)
- **권한**: 전체 시스템 관리

## 🔄 Git 관리

### 현재 상태
- ✅ **모든 변경사항 커밋 완료**
- ✅ **원격 저장소 푸시 완료**
- ✅ **디버깅 이슈 해결 완료**

### 브랜치 전략
- **main**: 프로덕션 배포 완료 상태
- **develop**: 개발 진행 중
- **feature/***: 기능별 개발 브랜치

## 📚 문서

- **[아키텍처 개요](ARCHITECTURE_OVERVIEW.md)** - 시스템 전체 구조
- **[AWS 배포 현황](AWS_DEPLOYMENT_STATUS.md)** - 상세 배포 정보
- **[디렉토리 구조](DIRECTORY_STRUCTURE.md)** - 프로젝트 구조
- **[코드 리뷰](docs/CODE_REVIEW.md)** - 개발 가이드
- **[디버깅 가이드](docs/DEBUGGING_GUIDE.md)** - 디버깅 완료 상태
- **[운영 가이드](docs/runbook.md)** - 운영 절차
- **[로그 쿼리](docs/log-queries.md)** - 모니터링 쿼리

## 🎯 프로젝트 목표

**GovChat**은 정부 재정 지원사업 정보를 AI로 분석하여 사용자에게 맞춤 매칭해주는 서비스입니다.

### 핵심 기능
1. **통합 데이터 수집**: 공공데이터 포털 API 연동
2. **AI 조건 추론**: 대화에서 매칭 조건 자동 추출
3. **원서치 시스템**: OpenSearch 기반 통합 검색
4. **점진적 프로필**: 대화 기반 사용자 프로필 완성

### 기술 스택
- **Frontend**: Next.js + TypeScript + Tailwind CSS
- **Backend**: AWS Lambda + Python 3.12
- **Database**: DynamoDB + OpenSearch Serverless
- **AI**: GPT-4 Mini + OpenAI Embeddings
- **Infrastructure**: AWS CDK + CloudFormation

---

**배포 상태**: ✅ 프로덕션 배포 완료  
**디버깅 상태**: ✅ 주요 이슈 해결 완료  
**다음 작업**: 외부 API 연동  
**최종 업데이트**: 2025-01-14