# GovChat 디렉토리 구조

## 📁 프로젝트 구조 개요

```
/home/ec2-user/gov-support-chat/
├── 📋 문서 및 설정
├── 🎨 프론트엔드 (Next.js)
├── ☁️ 인프라 (AWS CDK)
├── 🧪 테스트
├── 📁 로그 파일들
└── 🔧 설정 파일들
```

## 📋 문서 및 설정

```
.amazonq/                    # Amazon Q 설정
├── rules/                   # 코딩 규칙
│   ├── 00_baseline.md
│   ├── 01_project_rules.md
│   └── 02_frontend_rules.md
└── README.md

.github/                     # GitHub Actions
└── workflows/
    ├── ci-cd.yml           # 배포 파이프라인
    ├── ci.yml              # 테스트 파이프라인
    └── security-quality-check.yml

docs/                        # 프로젝트 문서
├── adr/                    # Architecture Decision Records
├── checklists/             # 체크리스트
├── ci/                     # CI/CD 문서
├── epics/                  # 에픽 문서
├── tickets/                # 티켓 문서
├── coadreview.md          # 코드 리뷰 가이드
├── log-queries.md         # 로그 쿼리
└── runbook.md             # 운영 가이드

prompts/                     # AI 프롬프트
├── build_phase.md
└── review_phase.md
```

## 🎨 프론트엔드 (Next.js)

```
frontend/
├── public/                  # 정적 파일
├── src/
│   ├── api/                # API 클라이언트
│   │   ├── api-client/
│   │   └── openapi.yaml
│   ├── app/                # Next.js App Router
│   │   ├── admin/          # 관리자 페이지
│   │   ├── auth/           # 인증 페이지
│   │   ├── chat/           # 챗봇 페이지
│   │   ├── matches/        # 매칭 결과
│   │   ├── mypage/         # 마이페이지
│   │   ├── onboarding/     # 온보딩
│   │   └── program/        # 프로그램 상세
│   ├── components/         # React 컴포넌트
│   ├── hooks/              # Custom Hooks
│   ├── lib/                # 유틸리티
│   └── types/              # TypeScript 타입
├── tests/                  # 프론트엔드 테스트
├── package.json
├── next.config.js
└── tailwind.config.ts
```

## ☁️ 인프라 (AWS CDK)

```
infra/
├── infra/                   # CDK 스택 정의
│   ├── __init__.py
│   └── infra_stack.py      # 메인 인프라 스택
├── layers/                  # Lambda 레이어
│   ├── layer_stack.py      # 레이어 스택
│   ├── build_layers.py     # 레이어 빌드
│   └── requirements-*.txt  # 의존성 파일들
├── lib/                     # 추가 스택들
│   ├── gist-upload-stack.ts
│   └── github-webhook-stack.ts
├── src/                     # Lambda 함수 소스코드
│   ├── functions/          # Lambda 핸들러들
│   │   ├── authorizer/     # JWT 인증 (Node.js)
│   │   ├── chatbot_handler.py      # 챗봇 핸들러
│   │   ├── search_handler.py       # 검색 핸들러
│   │   ├── match_handler.py        # 매칭 핸들러
│   │   ├── admin_handler.py        # 관리자 핸들러
│   │   ├── policy_handler.py       # 정책 CRUD
│   │   ├── user_profile_handler.py # 사용자 프로필
│   │   ├── user_auth_handler.py    # 사용자 인증
│   │   ├── extract_handler.py      # 데이터 추출
│   │   ├── error_handler.py        # 에러 처리
│   │   ├── response_builder.py     # 응답 빌더
│   │   └── logger_config.py        # 로깅 설정
│   ├── common/             # 공통 모듈
│   │   ├── cache_strategy.py
│   │   ├── circuit_breaker.py
│   │   ├── monitoring.py
│   │   ├── rate_limiter.py
│   │   └── xss_protection.py
│   ├── chatbot/            # 챗봇 엔진
│   │   └── conversation_engine.py
│   └── [Python 패키지들]   # 의존성 라이브러리들
├── tests/                   # 인프라 테스트
│   ├── fixtures/
│   └── unit/
├── app.py                   # CDK 앱 진입점
├── auth_stack.py           # 인증 스택
├── deploy.py               # 배포 스크립트
├── cdk.json                # CDK 설정
└── requirements.txt        # Python 의존성
```

## 🧪 테스트

```
tests/
├── e2e/                     # E2E 테스트 (Playwright)
│   ├── auth-flow.spec.js
│   ├── chat.spec.js
│   └── chatbotFlow.spec.js
├── test_admin_functions.py  # 관리자 기능 테스트
├── test_auth_enhanced.py    # 인증 테스트
├── test_chatbot.py         # 챗봇 테스트
├── test_health_check.py    # 헬스체크 테스트
├── test_integration.py     # 통합 테스트
├── test_security.py        # 보안 테스트
└── test_unified_chatbot.py # 통합 챗봇 테스트
```

## 🔧 설정 파일들

```
├── .gitignore              # Git 무시 파일
├── .pre-commit-config.yaml # Pre-commit 훅
├── pyproject.toml          # Python 프로젝트 설정
├── package.json            # Node.js 의존성
├── Makefile                # 빌드 명령어
├── cleanup.sh              # 정리 스크립트
├── lighthouse-budget.json  # 성능 예산
└── vitest.config.js        # 테스트 설정
```

## 📄 주요 문서들

```
├── README.md                    # 프로젝트 개요
├── ARCHITECTURE_OVERVIEW.md    # 아키텍처 개요
├── AWS_DEPLOYMENT_STATUS.md    # 배포 현황
├── CLEANUP_PLAN.md            # 정리 계획
└── DIRECTORY_STRUCTURE.md     # 이 문서
```

## 🎯 핵심 특징

### 🐍 백엔드: Python 기반
- **Lambda 함수들**: 모두 Python 3.12
- **CDK 스택**: Python으로 인프라 정의
- **테스트**: pytest 기반

### 🎨 프론트엔드: Next.js 기반
- **App Router**: 최신 Next.js 구조
- **TypeScript**: 타입 안전성
- **Tailwind CSS**: 스타일링

### ☁️ 인프라: AWS 서버리스
- **Lambda**: 서버리스 컴퓨팅
- **API Gateway**: REST API
- **DynamoDB**: NoSQL 데이터베이스
- **OpenSearch**: 벡터 검색
- **S3**: 파일 저장소

### 🧪 테스트: 다층 테스트
- **Unit Tests**: 개별 함수 테스트
- **Integration Tests**: 통합 테스트
- **E2E Tests**: 전체 플로우 테스트
- **Health Check**: 운영 모니터링

이 구조는 **마이크로서비스 아키텍처**와 **서버리스 패턴**을 따르며, **확장성**과 **유지보수성**을 고려하여 설계되었습니다.