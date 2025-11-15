import { test, expect } from '@playwright/test';

test.describe('Delete Resource E2E Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
    await page.evaluate(() => sessionStorage.clear());
  });

  test('should delete resource and verify UI updates', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');

    const resourceId = 'test-resource-123';
    await page.goto(`/resources/${resourceId}`);
    await expect(page.locator(`[data-resource-id="${resourceId}"]`)).toBeVisible();

    await page.click(`[data-resource-id="${resourceId}"] [data-action="delete"]`);
    await page.click('button.confirm-delete');

    await expect(page.locator(`[data-resource-id="${resourceId}"]`)).not.toBeVisible();
    await expect(page.locator('.notification.success')).toContainText('Resource deleted successfully');

    await page.reload();
    await expect(page.locator(`[data-resource-id="${resourceId}"]`)).not.toBeVisible();
  });

  test('should handle delete error gracefully', async ({ page }) => {
    await page.route('**/api/resources/*', route => {
      if (route.request().method() === 'DELETE') {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Failed to delete resource' })
        });
      } else {
        route.continue();
      }
    });

    await page.goto('/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');

    const resourceId = 'error-resource-456';
    await page.goto(`/resources/${resourceId}`);
    await expect(page.locator(`[data-resource-id="${resourceId}"]`)).toBeVisible();

    await page.click(`[data-resource-id="${resourceId}"] [data-action="delete"]`);
    await page.click('button.confirm-delete');

    await expect(page.locator('.notification.error')).toContainText('Failed to delete resource');
    await expect(page.locator(`[data-resource-id="${resourceId}"]`)).toBeVisible();
  });

  test.afterEach(async ({ page }) => {
    await page.evaluate(() => localStorage.clear());
    await page.evaluate(() => sessionStorage.clear());
    await page.context().clearCookies();
  });
});