# TICKET-001: Landing Page 구현

**우선순위**: High  
**스프린트**: T+1  
**담당자**: Frontend Team

## 요구사항

### 기능 명세
- Value proposition 섹션
- **Start Chat** CTA 버튼
- Screenshots carousel
- 반응형 디자인

### 기술 요구사항
- `export const revalidate = 3600` 적용
- SEO 메타태그 최적화
- Core Web Vitals 최적화

## Definition of Done

- [ ] 페이지 구현 완료
- [ ] Unit tests 작성 (>80% 커버리지)
- [ ] Playwright E2E 테스트 작성
- [ ] 성능 테스트 통과 (LCP < 2.5s)
- [ ] 접근성 테스트 통과 (WCAG 2.1 AA)
- [ ] 코드 리뷰 승인

## 테스트 시나리오

### Unit Tests
- 컴포넌트 렌더링 테스트
- CTA 버튼 클릭 이벤트
- 반응형 레이아웃 테스트

### E2E Tests
```typescript
test('Landing page CTA flow', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="start-chat-cta"]');
  await expect(page).toHaveURL('/auth/signin');
});
```

## 성능 목표
- LCP: < 2.5초
- FID: < 100ms
- CLS: < 0.1
- TTFB: < 200ms