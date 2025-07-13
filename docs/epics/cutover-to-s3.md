# Epic: S3 + CloudFront 마이그레이션

**목표**: Lambda SSR에서 S3 정적 호스팅으로 전환하여 비용 40% 절감 및 성능 향상

## 마일스톤

### T+1 Sprint: ISR 안정성 검증
- [ ] 핵심 페이지에 `revalidate=60` 적용
- [ ] 캐시 히트율 모니터링 설정
- [ ] 성능 베이스라인 측정

**완료 조건**: 캐시 히트율 > 85%, TTFB < 200ms

### T+2 Sprint: CloudFront 카나리 배포
- [ ] CloudFront Blue/Green 설정
- [ ] 10% 트래픽 카나리 배포
- [ ] 에러율 모니터링 (<0.1%)

**완료 조건**: 카나리 환경에서 7일간 안정 운영

### T+3 Sprint: S3 기본 오리진 전환
- [ ] S3 정적 호스팅 설정
- [ ] API 경로만 Lambda 유지
- [ ] DNS 전환 및 모니터링

**완료 조건**: 전체 트래픽 S3 처리, 비용 40% 절감 확인

## CloudFront Blue/Green Runbook

### 배포 절차
1. **Blue 환경 준비**
   ```bash
   aws cloudfront create-distribution --distribution-config blue-config.json
   ```

2. **트래픽 분할**
   ```bash
   aws cloudfront update-distribution --id DIST_ID --distribution-config canary-10.json
   ```

3. **모니터링 확인**
   - 에러율 < 0.1%
   - 응답시간 < 500ms
   - 가용성 > 99.9%

4. **롤백 절차**
   ```bash
   aws cloudfront update-distribution --id DIST_ID --distribution-config rollback.json
   ```

### 성공 메트릭
- **비용**: 40% 절감 (Lambda 실행 시간 감소)
- **성능**: TTFB 50% 개선
- **가용성**: 99.99% 유지

## 위험 요소 및 대응

| 위험 | 영향도 | 대응책 |
|------|--------|--------|
| ISR 캐시 무효화 실패 | 높음 | 수동 무효화 스크립트 준비 |
| API 경로 라우팅 오류 | 중간 | 헬스체크 강화 |
| DNS 전파 지연 | 낮음 | TTL 단축 (300초) |

## 참고 자료
- [AWS CloudFront Blue/Green 배포](https://aws.amazon.com/blogs/networking-and-content-delivery/achieving-zero-downtime-deployments-with-amazon-cloudfront-using-blue-green-continuous-deployments/)
- [Next.js ISR 가이드](https://nextjs.org/docs/pages/guides/incremental-static-regeneration)