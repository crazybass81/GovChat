import { test, expect } from '@playwright/test';

test('chat redirects unauth user', async ({ page }) => {
  await page.goto('/chat');
  await expect(page).toHaveURL(/auth\/signin/);
});

test('landing page loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('정부지원사업');
});

test('matches page loads', async ({ page }) => {
  await page.goto('/matches');
  await expect(page.locator('h1')).toContainText('매칭된 지원사업');
});

test('program detail page loads', async ({ page }) => {
  await page.goto('/program/1');
  await expect(page.locator('h1')).toContainText('AI 바우처');
});