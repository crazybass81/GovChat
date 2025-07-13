# GovChat 운영 Runbook

## 1. 시스템 개요

### SLA 목표
- **가용성**: 99.5% (월 3.6시간 다운타임 허용)
- **응답시간**: P95 < 1.2초
- **에러율**: < 2%
- **처리량**: 1000 RPS

### 주요 컴포넌트
- **API Gateway**: REST API 엔드포인트
- **Lambda Functions**: 4개 함수 (Chatbot, Search, Match, Extract)
- **DynamoDB**: 캐시 테이블
- **OpenSearch Serverless**: 벡터 검색
- **S3**: 데이터 저장소

## 2. 알람 대응 절차

### 2.1 Lambda 에러율 알람 (> 2%)

**증상**: `GovChat-{Function}-ErrorRate` 알람 발생

**즉시 대응**:
1. CloudWatch Logs에서 에러 로그 확인
2. X-Ray 트레이스에서 에러 패턴 분석
3. 일시적 에러인지 확인

**근본 원인 분석**:
- DynamoDB 스로틀링: `ProvisionedThroughputExceededException`
- OpenSearch 타임아웃: `ConnectTimeoutError`
- 메모리 부족: `Runtime.OutOfMemory`
- Cold Start 지연: 초기화 시간 > 10초

### 2.2 P95 지연시간 알람 (> 1초)

**증상**: `GovChat-{Function}-P95Latency` 알람 발생

**즉시 대응**:
1. Lambda 메트릭 확인
2. Cold Start 빈도 확인
3. 외부 의존성 지연 확인

### 2.3 DynamoDB 스로틀링 알람

**증상**: `GovChat-DynamoDB-Throttles` 알람 발생

**즉시 대응**:
1. DynamoDB 메트릭 확인
2. 핫 파티션 확인
3. 임시 조치 (Auto Scaling 설정 확인)

## 3. 정기 점검 절차

### 3.1 일일 점검 (매일 09:00)

**점검 항목**:
- [ ] 모든 Lambda 함수 정상 동작
- [ ] DynamoDB 스로틀링 없음
- [ ] OpenSearch 클러스터 상태 GREEN
- [ ] S3 버킷 용량 < 80%
- [ ] 캐시 히트율 > 70%

### 3.2 주간 점검 (매주 월요일)

**보안 점검**:
- [ ] IAM 역할 권한 검토
- [ ] KMS 키 로테이션 상태 확인
- [ ] VPC 보안 그룹 규칙 검토
- [ ] CloudTrail 로그 이상 활동 확인

## 4. 장애 복구 절차

### 4.1 Lambda 함수 장애
1. 이전 버전으로 롤백
2. 환경변수 확인 및 복구
3. 의존성 서비스 상태 확인

### 4.2 DynamoDB 장애
1. 테이블 상태 확인
2. 백업에서 복구 (필요시)
3. Lambda 함수에서 캐시 우회 모드 활성화

### 4.3 OpenSearch 장애
1. 컬렉션 상태 확인
2. 네트워크 정책 확인
3. 대체 검색 로직 활성화

## 5. 비상 연락처

### 온콜 담당자
- **Primary**: DevOps Team Lead
- **Secondary**: Backend Developer
- **Escalation**: CTO

## 6. 핵심 메트릭

**가용성**:
- `AWS/Lambda/Errors`
- `AWS/Lambda/Duration`
- `AWS/ApiGateway/4XXError`
- `AWS/ApiGateway/5XXError`

**성능**:
- `GovChat/CacheHitRate`
- `AWS/DynamoDB/ConsumedReadCapacityUnits`
- `AWS/Lambda/ConcurrentExecutions`

---

**문서 버전**: v1.0  
**최종 업데이트**: 2025-07-10