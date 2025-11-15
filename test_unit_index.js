import { test, expect } from '@playwright/test';

test('should render index.html with correct title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle('hack');
});

test('should have root div element', async ({ page }) => {
  await page.goto('/');
  const rootElement = await page.$('#root');
  expect(rootElement).not.toBeNull();
});

test('should load main.jsx module script', async ({ page }) => {
  await page.goto('/');
  const scriptElement = await page.$('script[type="module"]');
  expect(scriptElement).not.toBeNull();
  const src = await scriptElement.getAttribute('src');
  expect(src).toBe('/src/main.jsx');
});

test('should contain viewport meta tag', async ({ page }) => {
  await page.goto('/');
  const metaViewport = await page.$('meta[name="viewport"]');
  expect(metaViewport).not.toBeNull();
  const content = await metaViewport.getAttribute('content');
  expect(content).toBe('width=device-width, initial-scale=1.0');
});

test('should have correct charset meta tag', async ({ page }) => {
  await page.goto('/');
  const metaCharset = await page.$('meta[charset]');
  expect(metaCharset).not.toBeNull();
  const charset = await metaCharset.getAttribute('charset');
  expect(charset).toBe('UTF-8');
});