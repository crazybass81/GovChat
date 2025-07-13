# 02 Frontend Rules - Next.js

**날짜**: 2025-07-13  
**상태**: 강제 적용

## Static Page Revalidation Rule

**모든 정적 페이지는 반드시 `export const revalidate` 선언하거나 SSR 사유를 명시해야 함**

### ✅ 올바른 예시:

```typescript
// 정적 콘텐츠
export const revalidate = 3600; // 1시간

// 인증 필요 페이지
export const revalidate = 0; // 캐싱 방지

// SSR 필요한 경우
// SSR 사유: 실시간 데이터 표시 필요
export default function RealTimePage() { ... }
```

### ❌ 잘못된 예시:

```typescript
// revalidate 선언 없음
export default function SomePage() { ... }
```

## ISR 전환 가이드라인

1. **T+1 Sprint**: 핵심 페이지에 `revalidate=60` 적용
2. **T+2 Sprint**: CloudFront 카나리 배포 (10%)
3. **T+3 Sprint**: S3 기본 오리진 전환

## 성능 목표

- 정적 페이지: < 200ms TTFB
- 동적 페이지: < 500ms TTFB
- 캐시 히트율: > 85%