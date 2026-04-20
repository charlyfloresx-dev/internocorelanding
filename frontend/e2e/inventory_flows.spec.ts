import { test, expect } from '@playwright/test';

test.describe('Inventory Flows E2E Validation', () => {

  test.beforeEach(async ({ page }) => {
    // 1. Bypass Catalog Initialization to prevent the AuthInterceptor from reacting to 401/403s on unseeded DB ends
    await page.route('**/warehouses/', async route => route.fulfill({ status: 200, json: { status: 'success', data: [{ id: 'WH-TIJ', name: 'Tijuana', code: 'TIJ' }] } }));
    await page.route('**/concepts/', async route => route.fulfill({ status: 200, json: { status: 'success', data: [] } }));
    await page.route('**/uoms/', async route => route.fulfill({ status: 200, json: { status: 'success', data: [] } }));
    await page.route('**/categories/', async route => route.fulfill({ status: 200, json: { status: 'success', data: [] } }));
    await page.route('**/brands/', async route => route.fulfill({ status: 200, json: { status: 'success', data: [] } }));
    await page.route('**/dashboard/summary*', async route => route.fulfill({ status: 200, json: { status: 'success', data: { entries_24h: 0, outputs_24h: 0, transfers_24h: 0, pending_docs: 0 } } }));
    await page.route('**/admin/demo-reset*', async route => route.fulfill({ status: 200, json: { status: 'success' } }));
    await page.route('**/dashboard/mission-control*', async route => route.fulfill({ status: 200, json: { status: 'success', data: { valuation: { stock_yesterday: 0, total_usd: 0, variation_percentage: 0} } } }));
  });

  test('UC-INV-01 (Readiness Check): Show config modal when not ready', async ({ page }) => {
    // Mock Readiness to fail
    await page.route('**/api/v1/readiness', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            is_ready: false,
            status: 'CONFIG_PENDING',
            steps: [
              { name: 'Categorías', completed: true },
              { name: 'Almacenes', completed: false }
            ]
          }
        })
      });
    });

    // Navigate
    await page.goto('/inventory/dashboard');

    // Assert Modal
    await expect(page.getByText('Configuración Pendiente', { exact: false })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Almacenes')).toBeVisible();
  });

  test('UC-INV-02 (Anti-Fraude): Recibir button is disabled for self-transfers', async ({ page }) => {
    // Intercept to mock the document with my own userId
    await page.route('**/api/v1/inventory/documents*', async route => {
      // Need real user id, intercept the localStorage check
      const sessionStr = await page.evaluate(() => localStorage.getItem('_ic_auth_ctx')).catch(() => '{}');
      const session = JSON.parse(sessionStr || '{}');
      const userId = session.user_id || session.user?.id || 'UNKNOWN';

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: [
            {
              id: 'doc-123',
              folio: 'TR-001',
              type: 'Traspaso',
              status: 'PROCESSED',
              origin: 'TIJ',
              destination: 'SDY',
              date: new Date().toISOString(),
              created_by: userId // The dynamic ID read from Global Setup
            }
          ]
        })
      });
    });

    // Navigate first to have the origin ready to read localStorage
    await page.goto('/inventory/documents');

    const receiveButton = page.locator('button[title*="Restricción Anti-Fraude"]');
    await expect(receiveButton).toBeVisible({ timeout: 10000 });
    await expect(receiveButton).toBeDisabled();
  });

  test('UC-INV-03 (Money Pipe Validation): Format prices correctly', async ({ page }) => {
    // Mock movements ledger for MoneyPipe test
    await page.route('**/dashboard/movements*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: [
            {
              id: 'doc-124',
              folio: 'ENT-001',
              type: 'ENTRY',
              status: 'PROCESSED',
              origin: 'PROV-A',
              destination: 'TIJ',
              date: new Date().toISOString(),
              total_valuation: { amount: 1500.00, currency: 'USD' }
            }
          ]
        })
      });
    });

    await page.goto('/inventory/dashboard');

    await expect(page.getByText('$1,500.00 USD')).toBeVisible({ timeout: 10000 });
  });

});
