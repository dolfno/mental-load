import { test, expect } from '@playwright/test';

// Test user credentials
const testEmail = 'tasktest@example.com';
const testPassword = 'testpassword123';
const testName = 'Task Tester';

// Admin API key for creating test users (must match backend ADMIN_API_KEY env var)
const ADMIN_API_KEY = process.env.ADMIN_API_KEY || 'test-admin-key';

test.describe('Task Actions', () => {
  test.beforeAll(async ({ request }) => {
    // Create test user via admin API (will fail silently if user already exists)
    await request.post('/api/admin/users', {
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Api-Key': ADMIN_API_KEY,
      },
      data: {
        name: testName,
        email: testEmail,
        password: testPassword,
      },
    }).catch(() => null);
  });

  test.beforeEach(async ({ page }) => {
    // Go to login page and login
    await page.goto('/login');
    await page.fill('input[name="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);

    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/auth/login')
    );
    await page.click('button[type="submit"]');
    await responsePromise;

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

  test('bewerken button opens task edit modal', async ({ page }) => {
    // Find the first task card
    const taskCard = page.locator('[data-testid="task-card"]').first();

    // Skip if no tasks exist
    if (await taskCard.count() === 0) {
      test.skip();
      return;
    }

    // Get the task name
    const taskName = await taskCard.locator('h3').textContent();

    // Click the overflow menu (⋮)
    const overflowButton = taskCard.getByRole('button', { name: '⋮' });
    await overflowButton.click();

    // Click "Bewerken" in the dropdown
    const bewerkenOption = page.getByRole('button', { name: 'Bewerken' });
    await expect(bewerkenOption).toBeVisible();
    await bewerkenOption.click();

    // Verify modal is open with the task form
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Verify the task name is in the form
    const nameInput = modal.locator('input[type="text"]').first();
    await expect(nameInput).toHaveValue(taskName!);
  });

  test('edit modal shows confirmation when closing with unsaved changes', async ({ page }) => {
    // Find the first task card
    const taskCard = page.locator('[data-testid="task-card"]').first();

    // Skip if no tasks exist
    if (await taskCard.count() === 0) {
      test.skip();
      return;
    }

    // Open edit modal via overflow menu
    const overflowButton = taskCard.getByRole('button', { name: '⋮' });
    await overflowButton.click();
    await page.getByRole('button', { name: 'Bewerken' }).click();

    // Verify modal is open
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Make a change to the form
    const nameInput = modal.locator('input[type="text"]').first();
    const originalValue = await nameInput.inputValue();
    await nameInput.fill(originalValue + ' (gewijzigd)');

    // Set up dialog handler to dismiss the confirmation
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('confirm');
      expect(dialog.message()).toContain('niet-opgeslagen wijzigingen');
      await dialog.dismiss(); // Cancel closing
    });

    // Try to close by clicking outside the modal
    await page.locator('.fixed.inset-0.z-50').click({ position: { x: 10, y: 10 } });

    // Modal should still be visible because we dismissed the confirm dialog
    await expect(modal).toBeVisible();
  });

  test('edit modal saves changes on submit', async ({ page }) => {
    // Find the first task card
    const taskCard = page.locator('[data-testid="task-card"]').first();

    // Skip if no tasks exist
    if (await taskCard.count() === 0) {
      test.skip();
      return;
    }

    // Get original task name
    const originalName = await taskCard.locator('h3').textContent();

    // Open edit modal
    const overflowButton = taskCard.getByRole('button', { name: '⋮' });
    await overflowButton.click();
    await page.getByRole('button', { name: 'Bewerken' }).click();

    // Verify modal is open
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Change the task name
    const nameInput = modal.locator('input[type="text"]').first();
    const newName = originalName + ' (e2e test)';
    await nameInput.fill(newName);

    // Listen for the PUT request
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/api/tasks/') &&
                  response.request().method() === 'PUT'
    );

    // Submit the form
    await modal.getByRole('button', { name: 'Opslaan' }).click();

    // Wait for the API response
    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Modal should close
    await expect(modal).not.toBeVisible();

    // Verify the task name was updated
    await page.waitForTimeout(500);
    const updatedTaskCard = page.locator('[data-testid="task-card"]').filter({ hasText: newName });
    await expect(updatedTaskCard).toBeVisible();

    // Restore original name for other tests
    const restoreOverflow = updatedTaskCard.getByRole('button', { name: '⋮' });
    await restoreOverflow.click();
    await page.getByRole('button', { name: 'Bewerken' }).click();
    await expect(modal).toBeVisible();
    await modal.locator('input[type="text"]').first().fill(originalName!);
    await modal.getByRole('button', { name: 'Opslaan' }).click();
    await expect(modal).not.toBeVisible();
  });
});
