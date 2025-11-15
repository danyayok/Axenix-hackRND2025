import { test, expect } from '@playwright/test';

test.describe('User Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should allow user to login and logout successfully', async ({ page }) => {
    await page.click('text=Login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Welcome, testuser')).toBeVisible();
    await page.click('text=Logout');
    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Login')).toBeVisible();
  });

  test('should show error on invalid login credentials', async ({ page }) => {
    await page.click('text=Login');
    await page.fill('[name="username"]', 'invaliduser');
    await page.fill('[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    await expect(page.locator('.error-message')).toBeVisible();
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });

  test('should redirect unauthenticated user from protected route', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Please log in to continue')).toBeVisible();
  });
});