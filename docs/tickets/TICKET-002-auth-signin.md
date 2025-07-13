# TICKET-002: 로그인 페이지 구현

**우선순위**: High  
**스프린트**: T+1  
**담당자**: Auth Team

## 요구사항

### 기능 명세
- Kakao/Google/Naver OAuth 버튼
- 이메일/비밀번호 폴백 인증
- `callbackUrl` 리다이렉트 로직
- 에러 처리 및 사용자 피드백

### 기술 요구사항
- NextAuth.js v5 통합
- `export const revalidate = 0` (인증 페이지)
- CSRF 보호
- Rate limiting 적용

## Definition of Done

- [ ] OAuth 제공자 연동 완료
- [ ] 이메일 인증 플로우 구현
- [ ] Unit tests 작성 (>80% 커버리지)
- [ ] Playwright E2E 테스트 작성
- [ ] 보안 테스트 통과
- [ ] 코드 리뷰 승인

## 보안 요구사항

- PKCE 플로우 적용
- State 파라미터 검증
- Session 보안 강화
- XSS/CSRF 방지

## 테스트 시나리오

### E2E Tests
```typescript
test('OAuth login flow', async ({ page }) => {
  await page.goto('/auth/signin');
  await page.click('[data-testid="kakao-login"]');
  // OAuth 플로우 시뮬레이션
  await expect(page).toHaveURL('/chat');
});
```