import { chromium, FullConfig, request as playwrightRequest } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const apiContext = await playwrightRequest.newContext();
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('\n🌍 [Global Setup] Performing Real Auth Handshake...');

  try {
    // 1. Post to login
    const loginRes = await apiContext.post('http://localhost:8001/api/v1/auth/login', {
      data: { email: 'charly@interno.com', password: 'charly123' }
    });
    
    if (!loginRes.ok()) {
      throw new Error(`Login failed: ${loginRes.status()} ${await loginRes.text()}`);
    }

    const loginData = await loginRes.json();
    const selToken = loginData.data.selection_token;
    
    // Find Tijuana company or fallback
    const targetCompany = loginData.data.companies.find((c: any) => c.company_name.includes('Tijuana')) 
                          || loginData.data.companies[0];

    // 2. Select Company to get real JWT
    const selectRes = await apiContext.post('http://localhost:8001/api/v1/auth/select-company', {
      headers: {
        'Authorization': `Bearer ${selToken}`,
        'X-Selection-Token': selToken
      },
      data: { company_id: targetCompany.company_id }
    });
    
    if (!selectRes.ok()) {
      throw new Error(`Select company failed: ${selectRes.status()} ${await selectRes.text()}`);
    }

    const selectData = await selectRes.json();
    const finalAuthData = selectData.data;

    // 3. Set localStorage on the frontend domain
    await page.goto('http://localhost:4200/'); // Go to the app to set storage for this origin
    await page.evaluate((sessionData: any) => {
      localStorage.setItem('_ic_auth_ctx', JSON.stringify({
        ...sessionData,
        company_id: sessionData.company_id || sessionData.company?.id,
        user_id: sessionData.user?.id || sessionData.user_id,
        roles: sessionData.roles || []
      }));
    }, { ...finalAuthData, company_id: targetCompany.company_id });

    // 4. Save state
    await page.context().storageState({ path: 'storageState.json' });
    console.log('✅ [Global Setup] Storage state saved (Hybrid-Mock Ready)\n');
  } catch (err) {
    console.error('❌ [Global Setup] Failed to authenticate against Backend:', err);
    throw err;
  } finally {
    await apiContext.dispose();
    await browser.close();
  }
}

export default globalSetup;
