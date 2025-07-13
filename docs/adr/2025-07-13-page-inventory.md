# ADR-002: 페이지 및 기능 인벤토리

**날짜**: 2025-07-13  
**상태**: 승인됨  
**결정자**: 개발팀

## 컨텍스트

GovChat 시스템의 전체 페이지와 기능을 체계적으로 관리하고 추적하기 위해 완전한 인벤토리가 필요했습니다.

## 결정

다음과 같은 4개 카테고리로 페이지를 분류하여 관리하기로 결정했습니다.

### 2.1 Public & On-boarding

| Path                  | Key features                                                             | Status |
| --------------------- | ------------------------------------------------------------------------ | ------ |
| `/` (Landing)         | Value prop, **Start Chat** CTA, screenshots carousel                     | ✅     |
| `/auth/signin`        | Kakao/Google/Naver buttons, email fallback, `callbackUrl` redirect logic | ✅     |
| `/onboarding`         | 3-step consent wizard (privacy/data use) → writes to `consent-tbl`       | ❌     |
| `/privacy` · `/terms` | Markdown legal pages, last-updated timestamp                             | ❌     |

### 2.2 Core Application

| Path            | Functionality                                                                                   | Status |
| --------------- | ----------------------------------------------------------------------------------------------- | ------ |
| `/chat`         | Auth guard; if profile incomplete, bot collects data; finishes when ≥ 90% match or none remain | ✅     |
| `/matches`      | List of matched programmes → links to detail                                                    | ✅     |
| `/program/[id]` | Full programme details, eligibility tags, external apply link                                   | ✅     |
| `/mypage`       | User dashboard: contact info, profile completeness bar                                          | ✅     |

### 2.3 Admin Console

| Path                        | Features                                                    |
| --------------------------- | ----------------------------------------------------------- |
| `/admin`                    | Today's chats, new users, error rate, policy & API counters |
| `/admin/programs`           | Auto-sync list from external API; status badge editable     |
| `/admin/programs/[id]/edit` | Rich-text + JSON-schema editor                              |
| `/admin/users`              | Email search, role dropdown, force reset                    |
| `/admin/logs`               | CloudWatch Logs Insights iframe, filter by Lambda name      |

### 2.4 Utility & Error

- `/_health` – commit SHA + git hash
- `/404` – illustration + **Send Feedback**
- `/500` – error ID + Sentry deep link

## 결과

### 장점:
- 체계적인 기능 관리
- 개발 우선순위 명확화
- 테스트 커버리지 추적 가능

### 단점:
- 초기 설정 비용
- 지속적인 업데이트 필요

## 참고 자료

- [AWS UX Content Mapping](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless-network.html)
- [OWASP Serverless Top-10](https://docs.aws.amazon.com/systems-manager/latest/userguide/security-best-practices.html)