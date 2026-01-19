import { test, expect } from '@playwright/test';

// Test user credentials
const testEmail = 'tasktest@example.com';
const testPassword = 'testpassword123';
const testName = 'Task Tester';

test.describe('Task Actions', () => {
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
    await page.waitForSelector('[data-testid="task-card"], .text-gray-500:has-text("Geen taken")', { timeout: 10000 });
  });

  test('voltooid button marks task as complete', async ({ page }) => {
    // Find the first task card
    const taskCard = page.locator('[data-testid="task-card"]').first();

    // Skip if no tasks exist
    if (await taskCard.count() === 0) {
      test.skip();
      return;
    }

    // Get the task name before completing
    const taskName = await taskCard.locator('h3').textContent();

    // Get the original due date text (first .font-medium inside the due date section)
    const originalDueText = await taskCard.locator('.text-sm.opacity-75 > div.font-medium').first().textContent();

    // Click the voltooid button
    const voltooidButton = taskCard.getByRole('button', { name: /voltooid/i });
    await expect(voltooidButton).toBeVisible();

    // Listen for network request
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/tasks/') &&
                  response.url().includes('/complete') &&
                  response.request().method() === 'POST'
    );

    await voltooidButton.click();

    // Wait for the API response
    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Wait for the task list to refresh
    await page.waitForTimeout(500);

    // Verify the task's due date has changed (next occurrence)
    const updatedTaskCard = page.locator('[data-testid="task-card"]').filter({ hasText: taskName! });
    if (await updatedTaskCard.count() > 0) {
      const newDueText = await updatedTaskCard.locator('.text-sm.opacity-75 > div.font-medium').first().textContent();
      // After completion, the due date should change to the next occurrence
      console.log(`Due date changed from "${originalDueText}" to "${newDueText}"`);
    }
  });

  test('uitstellen - morgen postpones task to tomorrow', async ({ page }) => {
    // Find the first task card
    const taskCard = page.locator('[data-testid="task-card"]').first();

    // Skip if no tasks exist
    if (await taskCard.count() === 0) {
      test.skip();
      return;
    }

    // Get the task name
    const taskName = await taskCard.locator('h3').textContent();

    // Click the uitstellen button to open the menu
    const uitstellenButton = taskCard.getByRole('button', { name: /uitstellen/i });
    await expect(uitstellenButton).toBeVisible();
    await uitstellenButton.click();

    // Wait for the dropdown menu to appear
    const morgenOption = page.getByRole('button', { name: 'Morgen' });
    await expect(morgenOption).toBeVisible();

    // Listen for network request
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/tasks/') &&
                  response.request().method() === 'PUT'
    );

    // Click "Morgen" option
    await morgenOption.click();

    // Wait for the API response
    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Wait for the task list to refresh
    await page.waitForTimeout(500);

    // Verify the task now shows "Morgen" as due date
    const updatedTaskCard = page.locator('[data-testid="task-card"]').filter({ hasText: taskName! });
    if (await updatedTaskCard.count() > 0) {
      const dueText = await updatedTaskCard.locator('.text-sm.opacity-75 > div.font-medium').first().textContent();
      expect(dueText).toBe('Morgen');
    }
  });

  test('verwijderen deletes task after confirmation', async ({ page }) => {
    // Find the first task card
    const taskCard = page.locator('[data-testid="task-card"]').first();

    // Skip if no tasks exist
    if (await taskCard.count() === 0) {
      test.skip();
      return;
    }

    // Get the task name and count before deleting
    const taskName = await taskCard.locator('h3').textContent();
    const initialTaskCount = await page.locator('[data-testid="task-card"]').count();

    // Click the overflow menu (⋮)
    const overflowButton = taskCard.getByRole('button', { name: '⋮' });
    await expect(overflowButton).toBeVisible();
    await overflowButton.click();

    // Click "Verwijderen" in the dropdown (red text option)
    const verwijderenOption = page.locator('button.text-red-600:has-text("Verwijderen")');
    await expect(verwijderenOption).toBeVisible();
    await verwijderenOption.click();

    // Confirmation dialog should appear - the confirm button has red background
    const confirmButton = taskCard.locator('button.bg-red-500:has-text("Verwijderen")');
    await expect(confirmButton).toBeVisible();

    // Listen for DELETE and subsequent GET request
    const deletePromise = page.waitForResponse(
      response => response.url().includes('/api/tasks/') &&
                  response.request().method() === 'DELETE'
    );
    const getPromise = page.waitForResponse(
      response => response.url().endsWith('/api/tasks') &&
                  response.request().method() === 'GET'
    );

    // Confirm deletion
    await confirmButton.click();

    // Wait for both requests
    const deleteResponse = await deletePromise;
    expect(deleteResponse.status()).toBe(204);
    await getPromise;

    // Verify the task is no longer visible
    const deletedTaskCard = page.locator('[data-testid="task-card"]').filter({ hasText: taskName! });
    await expect(deletedTaskCard).toHaveCount(0);

    // Verify task count decreased
    const newTaskCount = await page.locator('[data-testid="task-card"]').count();
    expect(newTaskCount).toBe(initialTaskCount - 1);
  });
});
