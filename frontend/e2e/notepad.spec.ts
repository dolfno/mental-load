import { test, expect } from '@playwright/test';

// Test user credentials
const testEmail = 'notepadtest@example.com';
const testPassword = 'testpassword123';
const testName = 'Notepad Tester';

test.describe('Notepad', () => {
  test.beforeEach(async ({ page }) => {
    // Go to login page first
    await page.goto('/login');

    // Try to register - if user already exists, this will fail and we'll login
    const registerResponse = await page.request.post('/api/auth/register', {
      data: { name: testName, email: testEmail, password: testPassword }
    }).catch(() => null);

    if (registerResponse?.ok()) {
      // New user registered, store token and reload
      const data = await registerResponse.json();
      await page.evaluate((token) => localStorage.setItem('auth_token', token), data.access_token);
      await page.goto('/');
    } else {
      // User exists, login via form
      await page.fill('input[name="email"]', testEmail);
      await page.fill('input[name="password"]', testPassword);

      const responsePromise = page.waitForResponse(
        response => response.url().includes('/api/auth/login')
      );
      await page.click('button[type="submit"]');
      await responsePromise;
    }

    // Wait for dashboard to load
    await expect(page).toHaveURL('/', { timeout: 10000 });
  });

  test('can navigate to notepad page', async ({ page }) => {
    // Click the Kladblok link in navigation
    await page.click('nav a:has-text("Kladblok")');

    // Should be on the notepad page
    await expect(page).toHaveURL('/kladblok');
    await expect(page.locator('h2')).toContainText('Kladblok');
  });

  test('can enter and save notes', async ({ page }) => {
    // Navigate to notepad
    await page.goto('/kladblok');
    await expect(page.locator('h2')).toContainText('Kladblok');

    // Generate unique text for this test run
    const uniqueText = `Test note ${Date.now()}`;

    // Find the textarea and enter text
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible();
    await textarea.fill(uniqueText);

    // Wait for auto-save (1 second debounce + network)
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/notes') &&
                  response.request().method() === 'PUT'
    );
    await responsePromise;

    // Should show "Opgeslagen om" text
    await expect(page.locator('text=Opgeslagen om')).toBeVisible({ timeout: 5000 });
  });

  test('notes persist after page refresh', async ({ page }) => {
    // Navigate to notepad
    await page.goto('/kladblok');
    await expect(page.locator('h2')).toContainText('Kladblok');

    // Generate unique text for this test run
    const uniqueText = `Persistent note ${Date.now()}`;

    // Enter text
    const textarea = page.locator('textarea');
    await textarea.fill(uniqueText);

    // Wait for auto-save
    const savePromise = page.waitForResponse(
      response => response.url().includes('/api/notes') &&
                  response.request().method() === 'PUT'
    );
    await savePromise;

    // Wait a bit for save to complete
    await page.waitForTimeout(500);

    // Refresh the page
    await page.reload();

    // Wait for page to load
    await expect(page.locator('h2')).toContainText('Kladblok');

    // Verify the text is still there
    await expect(textarea).toHaveValue(uniqueText);
  });

  test('shows last updated timestamp', async ({ page }) => {
    // Navigate to notepad
    await page.goto('/kladblok');
    await expect(page.locator('h2')).toContainText('Kladblok');

    // Should show either "Laatst bewerkt" or "Opgeslagen om" timestamp
    const timestampText = page.locator('text=/Laatst bewerkt|Opgeslagen om/');
    await expect(timestampText).toBeVisible({ timeout: 5000 });
  });
});
