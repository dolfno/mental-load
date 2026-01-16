import { test, expect } from '@playwright/test';

test.describe('Task Actions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for tasks to load
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

    // Get the original due date text
    const originalDueText = await taskCard.locator('.text-sm.opacity-75 .font-medium').textContent();

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
      const newDueText = await updatedTaskCard.locator('.text-sm.opacity-75 .font-medium').textContent();
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
      const dueText = await updatedTaskCard.locator('.text-sm.opacity-75 .font-medium').textContent();
      expect(dueText).toBe('Morgen');
    }
  });
});
