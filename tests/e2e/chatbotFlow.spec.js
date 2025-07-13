import { test, expect } from '@playwright/test';

// 챗봇 플로우 테스트 시나리오: 로그인 -> 채팅 -> 로그아웃
// 이 테스트는 챗봇 애플리케이션의 엔드 투 엔드 기능을 검증합니다

test('Chatbot flow: login -> chat -> logout', async ({ page }) => {
    // 로그인 페이지로 이동
    await page.goto('/login');

    // 사용자 이름과 비밀번호를 입력하고 로그인 버튼 클릭
    await page.fill('#username', 'testuser');
    await page.fill('#password', 'password123');
    await page.click('#login-button');

    // 로그인 성공 후 대시보드로 리디렉션되는지 확인
    await expect(page).toHaveURL('/dashboard');

    // 대시보드 링크를 통해 챗봇 페이지로 이동
    await page.click('#chatbot-link');

    // 챗봇과 상호작용: 메시지 보내기
    await page.fill('#chat-input', 'Hello, chatbot!');
    await page.click('#send-button');

    // 챗봇이 사용자 메시지에 올바르게 응답하는지 확인
    const response = await page.locator('#chat-response').textContent();
    expect(response).toContain('Hello, testuser!');

    // 로그아웃 버튼 클릭하여 로그아웃 수행
    await page.click('#logout-button');

    // 로그아웃 후 로그인 페이지로 리디렉션되는지 확인
    await expect(page).toHaveURL('/login');
});
