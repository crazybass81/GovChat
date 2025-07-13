const { test, expect } = require('@playwright/test');

test.describe('Authentication Flow', () => {
  test('user signup and login flow', async ({ page }) => {
    // Navigate to signup page
    await page.goto('/auth/signin');
    
    // Mock API responses for testing
    await page.route('**/auth/user/signup', async route => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'User created successfully' })
      });
    });
    
    await page.route('**/auth/user/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          token: 'mock-jwt-token',
          user: { email: 'test@example.com', name: 'Test User' }
        })
      });
    });
    
    // Test signup form (if available)
    const signupButton = page.locator('text=회원가입');
    if (await signupButton.isVisible()) {
      await signupButton.click();
      
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'testpassword123');
      await page.fill('input[name="name"]', 'Test User');
      
      await page.click('button[type="submit"]');
      
      // Wait for success message or redirect
      await expect(page.locator('text=성공')).toBeVisible({ timeout: 5000 });
    }
    
    // Test login
    await page.goto('/auth/signin');
    
    // Use social login buttons (mocked)
    const kakaoButton = page.locator('text=Continue with Kakao');
    if (await kakaoButton.isVisible()) {
      await kakaoButton.click();
      
      // Should redirect to chat page after successful login
      await expect(page).toHaveURL('/chat');
    }
  });
  
  test('admin login flow', async ({ page }) => {
    await page.goto('/admin');
    
    // Mock admin auth
    await page.route('**/auth/admin/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          token: 'mock-admin-jwt-token',
          admin: { admin_id: 'admin123', role: 'admin' }
        })
      });
    });
    
    // Should redirect to admin login if not authenticated
    await expect(page).toHaveURL(/.*admin.*login/);
    
    // Fill admin login form
    await page.fill('input[name="admin_id"]', 'admin123');
    await page.fill('input[type="password"]', 'adminpassword');
    await page.click('button[type="submit"]');
    
    // Should redirect to admin dashboard
    await expect(page).toHaveURL('/admin');
    await expect(page.locator('text=Dashboard')).toBeVisible();
  });
});