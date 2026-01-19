import { test, expect } from '@playwright/test';

// Generate unique identifiers for each test run to avoid conflicts
let testEmail: string;
let testName: string;
const testPassword = 'testpassword123';

// Admin API key for creating test users (must match backend ADMIN_API_KEY env var)
const ADMIN_API_KEY = process.env.ADMIN_API_KEY || 'test-admin-key';

test.describe('Authentication', () => {
  test.beforeAll(async ({ request }) => {
    // Generate unique email and name at the start of test suite
    const uniqueId = `${Date.now()}-${Math.random().toString(36).substring(7)}`;
    testEmail = `test-${uniqueId}@example.com`;
    testName = `Test User ${uniqueId}`;

    // Create test user via admin API
    const response = await request.post('/api/admin/users', {
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Api-Key': ADMIN_API_KEY,
      },
      data: {
        name: testName,
        email: testEmail,
        password: testPassword,
      },
    });

    // User creation should succeed (201) or already exist (400)
    expect([201, 400]).toContain(response.status());
  });

  test.beforeEach(async ({ context }) => {
    // Clear all storage before each test
    await context.clearCookies();
  });

  test('redirects to login when not authenticated', async ({ page }) => {
    // Clear localStorage and then navigate
    await page.addInitScript(() => localStorage.clear());
    await page.goto('/', { waitUntil: 'networkidle' });

    // Should be redirected to login page
    await expect(page).toHaveURL('/login');
    await expect(page.locator('h2')).toContainText('Inloggen');
  });

  test('login page does not show register link', async ({ page }) => {
    await page.goto('/login');

    // Should not have a register link
    await expect(page.locator('a[href="/register"]')).not.toBeVisible();
  });

  test('register page shows disabled message', async ({ page }) => {
    await page.goto('/register');

    // Should show the disabled message
    await expect(page.locator('h2')).toContainText('Registreren');
    await expect(page.locator('.bg-amber-50')).toBeVisible();
    await expect(page.locator('.text-amber-700')).toContainText('Registratie is uitgeschakeld');

    // Should have link back to login
    await expect(page.locator('a[href="/login"]')).toBeVisible();
  });

  test('can logout', async ({ page }) => {
    // First login
    await page.goto('/login');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.click('button[type="submit"]');

    // Wait for dashboard
    await expect(page).toHaveURL('/');

    // Click logout button
    await page.click('button:has-text("Uitloggen")');

    // Should be redirected to login
    await expect(page).toHaveURL('/login');
  });

  test('can login with existing account', async ({ page }) => {
    await page.goto('/login');

    // Fill in login form
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);

    // Submit form
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/auth/login') &&
                  response.request().method() === 'POST'
    );

    await page.click('button[type="submit"]');

    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Should be redirected to dashboard
    await expect(page).toHaveURL('/');

    // Should see user name in header
    await expect(page.locator('header')).toContainText(testName);
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');

    // Wait for the API response
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/auth/login')
    );

    await page.click('button[type="submit"]');
    await responsePromise;

    // Should show error message
    await expect(page.locator('.bg-red-50')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.text-red-700')).toContainText('Ongeldige inloggegevens');

    // Should stay on login page
    await expect(page).toHaveURL('/login');
  });

  test('stays logged in after page refresh', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);

    // Wait for the API response
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/auth/login') &&
                  response.request().method() === 'POST'
    );

    await page.click('button[type="submit"]');

    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Wait for dashboard
    await expect(page).toHaveURL('/', { timeout: 10000 });
    await expect(page.locator('header')).toContainText(testName);

    // Refresh page
    await page.reload();

    // Should still be on dashboard (not redirected to login)
    await expect(page).toHaveURL('/');
    await expect(page.locator('header')).toContainText(testName);
  });

  test('protected routes require authentication', async ({ page }) => {
    // Clear any existing auth
    await page.goto('/login');
    await page.evaluate(() => localStorage.removeItem('auth_token'));

    // Try to access admin page directly
    await page.goto('/beheer');

    // Should be redirected to login
    await expect(page).toHaveURL('/login');
  });
});
