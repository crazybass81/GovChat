# CloudWatch Log Insights 쿼리 모음

## Lambda 성능 분석

### 1. 평균 응답시간 추이
```sql
fields @timestamp, @duration
| filter @type = "REPORT"
| stats avg(@duration), max(@duration), min(@duration) by bin(5m)
| sort @timestamp desc
```

### 2. 메모리 사용량 분석
```sql
fields @timestamp, @maxMemoryUsed, @memorySize
| filter @type = "REPORT"
| stats avg(@maxMemoryUsed), max(@maxMemoryUsed) by bin(5m)
| sort @timestamp desc
```

### 3. Cold Start 빈도
```sql
fields @timestamp, @message
| filter @message like /INIT_START/
| stats count() by bin(5m)
| sort @timestamp desc
```

## 에러 분석

### 4. 에러 패턴 분석
```sql
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by bin(5m)
| sort @timestamp desc
```

### 5. 특정 에러 유형별 분석
```sql
fields @timestamp, @message
| filter @message like /ProvisionedThroughputExceededException/
| stats count() by bin(1h)
| sort @timestamp desc
```

### 6. 타임아웃 에러 분석
```sql
fields @timestamp, @message
| filter @message like /Task timed out/
| stats count() by bin(5m)
| sort @timestamp desc
```

## 비즈니스 메트릭

### 7. 캐시 히트율 분석
```sql
fields @timestamp, @message
| filter @message like /cache_hit/ or @message like /cache_miss/
| stats count() by cache_result
```

### 8. API 엔드포인트별 사용량
```sql
fields @timestamp, @message
| filter @message like /POST/
| parse @message /POST (?<endpoint>\/\w+)/
| stats count() by endpoint
| sort count desc
```

### 9. 사용자 세션 분석
```sql
fields @timestamp, @message
| filter @message like /session_start/ or @message like /session_end/
| parse @message /user_id: (?<user_id>\w+)/
| stats count() by user_id
| sort count desc
```

## 보안 모니터링

### 10. 의심스러운 IP 활동
```sql
fields @timestamp, @message
| filter @message like /403/ or @message like /401/
| parse @message /sourceIPAddress: (?<ip>\d+\.\d+\.\d+\.\d+)/
| stats count() by ip
| sort count desc
| limit 20
```

### 11. 비정상적인 요청 패턴
```sql
fields @timestamp, @message
| filter @message like /rate_limit_exceeded/
| parse @message /user_id: (?<user_id>\w+)/
| stats count() by user_id
| sort count desc
```

## 성능 최적화

### 12. 느린 쿼리 분석
```sql
fields @timestamp, @message, @duration
| filter @message like /query_duration/
| parse @message /query_duration: (?<query_time>\d+)/
| filter query_time > 1000
| stats avg(query_time), max(query_time) by bin(5m)
```

### 13. DynamoDB 스로틀링 패턴
```sql
fields @timestamp, @message
| filter @message like /ThrottlingException/
| stats count() by bin(5m)
| sort @timestamp desc
```

### 14. OpenSearch 응답시간
```sql
fields @timestamp, @message
| filter @message like /opensearch_query/
| parse @message /response_time: (?<response_time>\d+)/
| stats avg(response_time), max(response_time) by bin(5m)
```

## 사용자 경험

### 15. 대화 세션 길이 분석
```sql
fields @timestamp, @message
| filter @message like /conversation_length/
| parse @message /turns: (?<turns>\d+)/
| stats avg(turns), max(turns), min(turns) by bin(1h)
```

### 16. 매칭 성공률
```sql
fields @timestamp, @message
| filter @message like /matching_result/
| parse @message /success: (?<success>\w+)/
| stats count() by success
```

### 17. 응답 만족도
```sql
fields @timestamp, @message
| filter @message like /user_feedback/
| parse @message /rating: (?<rating>\d+)/
| stats avg(rating), count() by bin(1h)
```

## 운영 메트릭

### 18. 함수별 실행 빈도
```sql
fields @timestamp, @message
| filter @type = "START"
| parse @logStream /\/aws\/lambda\/(?<function_name>[\w-]+)/
| stats count() by function_name
| sort count desc
```

### 19. 동시 실행 수 모니터링
```sql
fields @timestamp, @message
| filter @message like /concurrent_executions/
| parse @message /count: (?<concurrent>\d+)/
| stats max(concurrent) by bin(5m)
```

### 20. 비용 최적화 분석
```sql
fields @timestamp, @billedDuration, @memorySize
| filter @type = "REPORT"
| stats sum(@billedDuration * @memorySize) / 1000000 as cost_units by bin(1h)
| sort @timestamp desc
```

---

**사용법**:
1. AWS Console > CloudWatch > Logs > Insights
2. 로그 그룹 선택: `/aws/lambda/GovChat-*`
3. 위 쿼리 복사하여 실행
4. 시간 범위 조정하여 분석

**주의사항**:
- 쿼리 실행 시 비용 발생 (스캔된 데이터량 기준)
- 대용량 로그 분석 시 시간 범위를 좁혀서 실행
- 정기적으로 쿼리 결과를 대시보드에 저장하여 재사용