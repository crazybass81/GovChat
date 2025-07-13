import { test, expect } from '@playwright/test';

test('Chat page functionality', async ({ page }) => {
    await page.goto('/chat');
    await expect(page.locator('h1')).toHaveText('Welcome to the Chat Page');

    const addButton = page.locator('button', { hasText: 'Add Message' });
    await addButton.click();

    const messages = page.locator('ul > li');
    await expect(messages).toHaveCount(1);
    await expect(messages.first()).toHaveText('New message');
});
