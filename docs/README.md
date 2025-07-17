# 📚 GovChat 문서 가이드

## 📋 문서 구조

### 🎯 프로젝트 현황
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - 📊 프로젝트 종합 현황 보고서
- **[CODE_REVIEW.md](CODE_REVIEW.md)** - 📝 개발 가이드 및 코드 리뷰

### 🛠️ 운영 가이드
- **[runbook.md](runbook.md)** - 🚨 운영 절차 및 장애 대응
- **[log-queries.md](log-queries.md)** - 🔍 CloudWatch 로그 쿼리 모음

### 📐 아키텍처 및 설계
- **[adr/](adr/)** - Architecture Decision Records
  - 2025-01-13-auth-oidc.md
  - 2025-07-12-auth-oidc.md  
  - 2025-07-13-page-inventory.md

### 🎫 작업 관리
- **[tickets/](tickets/)** - 개별 작업 티켓들
  - TICKET-001-landing-page.md
  - TICKET-002-auth-signin.md

### 📊 체크리스트 및 절차
- **[checklists/](checklists/)** - 코드 리뷰 체크리스트
- **[ci/](ci/)** - CI/CD 파이프라인 문서
- **[epics/](epics/)** - 대규모 기능 개발 계획

### 📦 아카이브
- **[archive/](archive/)** - 이전 버전 문서들
  - IMPLEMENTATION_STATUS.md (구 구현 현황)

## 🎯 현재 상태 (2025-07-15)

### ✅ 완료
- AWS 배포 완료 (4개 스택)
- Lambda 함수 11개 정상 동작
- 모든 API 엔드포인트 정상화
- 문서 구조 정리 및 통합

### 🚨 다음 작업
1. **환경변수 설정** - OpenAI API 키 등
2. **OpenSearch 인덱스 생성** - 벡터 검색 활성화
3. **실제 데이터 동기화** - 정책 데이터 수집

### 📊 진행률
- **전체 진행률**: 90%
- **배포 상태**: 완료
- **핵심 기능**: 구조 완성

## 📖 문서 사용 가이드

### 🔍 상황별 문서 찾기

#### 프로젝트 전체 현황을 알고 싶다면
→ **[PROJECT_STATUS.md](PROJECT_STATUS.md)**

#### 개발 작업을 시작하려면
→ **[CODE_REVIEW.md](CODE_REVIEW.md)**

#### 시스템 장애가 발생했다면
→ **[runbook.md](runbook.md)**

#### 로그를 분석하려면
→ **[log-queries.md](log-queries.md)**

#### 아키텍처를 이해하려면
→ **[../ARCHITECTURE_OVERVIEW.md](../ARCHITECTURE_OVERVIEW.md)**

#### 배포 상태를 확인하려면
→ **[../AWS_DEPLOYMENT_STATUS.md](../AWS_DEPLOYMENT_STATUS.md)**

### 📝 문서 업데이트 규칙

1. **실시간 업데이트**: 배포나 주요 변경 시 즉시 문서 업데이트
2. **버전 관리**: 모든 문서 변경사항은 Git으로 추적
3. **명확한 상태**: 완료/진행중/계획 상태를 명확히 표시
4. **날짜 기록**: 모든 문서에 작성/수정 날짜 기록

### 🎯 문서 품질 기준

- **정확성**: 현재 시스템 상태와 일치
- **완전성**: 필요한 정보 누락 없음
- **명확성**: 기술적 배경 없이도 이해 가능
- **실용성**: 실제 작업에 도움이 되는 내용

## 🔗 관련 문서 링크

### 프로젝트 루트 문서
- **[README.md](../README.md)** - 프로젝트 메인 개요
- **[ARCHITECTURE_OVERVIEW.md](../ARCHITECTURE_OVERVIEW.md)** - 시스템 아키텍처
- **[AWS_DEPLOYMENT_STATUS.md](../AWS_DEPLOYMENT_STATUS.md)** - AWS 배포 현황
- **[DIRECTORY_STRUCTURE.md](../DIRECTORY_STRUCTURE.md)** - 프로젝트 구조

### 외부 리소스
- **AWS Console**: CloudWatch, Lambda, DynamoDB 모니터링
- **GitHub Repository**: 소스 코드 및 이슈 트래킹
- **API 엔드포인트**: https://l2iyczn1ge.execute-api.us-east-1.amazonaws.com/prod/

---

**마지막 업데이트**: 2025-07-15  
**다음 검토**: 주요 작업 완료 시  
**문서 관리자**: 개발팀