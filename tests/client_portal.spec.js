const { test, expect } = require("@playwright/test");

const baseURL = process.env.CLIENT_PORTAL_BASE_URL || "https://erpnext.77.237.244.169.sslip.io";
const clientUser = process.env.CLIENT_PORTAL_USER || "alpha.client@example.test";
const clientPassword = process.env.CLIENT_PORTAL_PASSWORD;

if (!clientPassword) {
  throw new Error("CLIENT_PORTAL_PASSWORD must be set in the environment");
}

const portalPages = [
  "/client/receiving-notice/list",
  "/client/products/list",
  "/client/product-import/list",
  "/client/product-export",
  "/client/inventory/list",
  "/client/shipment-request/list",
  "/client/shipment-tracking",
  "/client/discrepancies",
  "/client/discrepancy-instruction/list",
];

const navLabels = [
  "Receiving Notices",
  "Products",
  "Product Imports",
  "Product Export",
  "Inventory",
  "Shipment Requests",
  "Discrepancies",
  "Shipment Tracking",
  "Discrepancy Instructions",
];
const navTargets = {
  "Receiving Notices": "/client/receiving-notice/list",
  Products: "/client/products/list",
  "Product Imports": "/client/product-import/list",
  "Product Export": "/client/product-export",
  Inventory: "/client/inventory/list",
  "Shipment Requests": "/client/shipment-request/list",
  Discrepancies: "/client/discrepancies",
  "Shipment Tracking": "/client/shipment-tracking",
  "Discrepancy Instructions": "/client/discrepancy-instruction/list",
};
const expectedPageText = {
  "/client/receiving-notice/list": ["ASN-ALPHA-001", "ASN-ALPHA-002", "ASN-ALPHA-003"],
  "/client/products/list": ["ALPHA-001", "ALPHA-002", "ALPHA-003"],
  "/client/product-import/list": ["Download Import Template CSV"],
  "/client/product-export": ["Download Products CSV", "Download Import Template CSV"],
  "/client/inventory/list": ["ALPHA-001", "ALPHA-002", "ALPHA-003"],
  "/client/shipment-request/list": ["SHIP-ALPHA-001", "SHIP-ALPHA-002"],
  "/client/shipment-tracking": ["SHIP-ALPHA-001", "SHIP-ALPHA-002"],
  "/client/discrepancies": ["ASN-ALPHA-001", "ALPHA-002", "Quantity Difference"],
  "/client/discrepancy-instruction/list": ["ALPHA-002"],
};

async function collectPortalProblems(page, problems) {
  page.on("console", (message) => {
    const text = message.text();
    if (/Failed to load resource: the server responded with a status of 403/i.test(text)) return;
    if (/not permitted|no permission|permissionerror|403/i.test(text)) {
      problems.push(`console ${message.type()}: ${text}`);
    }
  });

  page.on("response", async (response) => {
    const url = response.url();
    if (response.status() >= 400) {
      let body = "";
      try {
        body = (await response.text()).slice(0, 600);
      } catch {
        body = "<unreadable body>";
      }
      problems.push(`response ${response.status()} ${url}: ${body}`);
    }
  });
}

async function assertPortalPage(page, path, problems) {
  await page.goto(`${baseURL}${path}`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1000);

  const bodyText = await page.locator("body").innerText();
  if (/not permitted|no permission|page not found/i.test(bodyText)) {
    problems.push(`body ${path}: ${bodyText.slice(0, 800)}`);
  }

  for (const text of expectedPageText[path] || []) {
    if (!bodyText.includes(text)) {
      problems.push(`body ${path}: missing demo record text ${text}`);
    }
  }

  for (const label of navLabels) {
    const link = page.getByRole("link", { name: label }).first();
    if (!(await link.isVisible().catch(() => false))) {
      problems.push(`body ${path}: missing nav label ${label}`);
      continue;
    }

    const href = await link.getAttribute("href");
    if (href !== navTargets[label]) {
      problems.push(`body ${path}: nav label ${label} points to ${href}`);
    }
  }

  const navCount = await page.locator("[data-client-portal-nav]").count();
  if (navCount !== 1) {
    problems.push(`body ${path}: expected one portal nav, found ${navCount}`);
  }

  if (path === "/client/products/list") {
    const clientColumn = page.locator(".web-list-table table th", { hasText: /^Client$/ });
    if ((await clientColumn.count()) > 0) {
      problems.push("body /client/products/list: client column should be hidden in portal list");
    }
    if (bodyText.includes("Demo Client Alpha")) {
      problems.push("body /client/products/list: client name should not be shown in portal list");
    }
  }
}

test("client portal pages render without permission errors", async ({ page }) => {
  const problems = [];
  await collectPortalProblems(page, problems);

  const loginResponse = await page.context().request.post(`${baseURL}/api/method/login`, {
    form: { usr: clientUser, pwd: clientPassword },
  });
  expect(loginResponse.ok()).toBeTruthy();
  expect(await loginResponse.json()).toMatchObject({ message: "No App" });

  for (const path of portalPages) {
    await assertPortalPage(page, path, problems);
  }

  expect(problems).toEqual([]);
});

test("client portal browser login persists across portal pages", async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  const problems = [];
  await collectPortalProblems(page, problems);

  await page.goto(`${baseURL}/login?redirect-to=%2Fclient%2Freceiving-notice%2Flist`);
  await page.waitForLoadState("networkidle");

  await page.locator("#login_email").fill(clientUser);
  await page.locator("#login_password").fill(clientPassword);
  await Promise.all([
    page.waitForURL((url) => url.pathname !== "/login", { timeout: 15000 }),
    page.locator(".btn-login").click(),
  ]);
  await page.waitForLoadState("networkidle");

  const loginPath = new URL(page.url()).pathname;
  if (/^\/(desk|app)(\/|$)/.test(loginPath)) {
    problems.push(`browser login redirected portal user to Desk: ${page.url()}`);
  }

  await assertPortalPage(page, "/client/receiving-notice/list", problems);

  const sidCookie = (await context.cookies(baseURL)).find((cookie) => cookie.name === "sid");
  if (!sidCookie) {
    problems.push("browser login did not create sid cookie");
  } else if (sidCookie.expires <= Math.floor(Date.now() / 1000) + 3600) {
    problems.push(`sid cookie is not persistent enough: expires=${sidCookie.expires}`);
  }

  const secondPage = await context.newPage();
  await collectPortalProblems(secondPage, problems);
  await assertPortalPage(secondPage, "/client/inventory/list", problems);

  const secondBody = await secondPage.locator("body").innerText();
  if (/login|email.*password/i.test(secondBody)) {
    problems.push("second portal page in same browser context asked for login again");
  }

  await context.close();
  expect(problems).toEqual([]);
});

test("receiving notice form auto-fills client reference", async ({ page }) => {
  const problems = [];
  await collectPortalProblems(page, problems);

  const loginResponse = await page.context().request.post(`${baseURL}/api/method/login`, {
    form: { usr: clientUser, pwd: clientPassword },
  });
  expect(loginResponse.ok()).toBeTruthy();

  await page.goto(`${baseURL}/client/receiving-notice/new`);
  await page.waitForLoadState("networkidle");

  const referenceInput = page
    .locator('input[data-fieldname="external_reference"], input[name="external_reference"], [data-fieldname="external_reference"] input')
    .first();
  await expect(referenceInput).toBeVisible();
  await expect(referenceInput).toHaveValue(/^ALPHA-IN-\d{8}-\d{3}$/, { timeout: 10000 });
  await expect(page.locator("#client-product-picker")).toBeVisible({ timeout: 10000 });
  await page.locator("#client-product-picker-search").fill("ALPHA-001");
  await expect(page.locator("#client-product-picker-results")).toContainText("ALPHA-001", { timeout: 10000 });

  expect(problems).toEqual([]);
});

test("shipment request form auto-fills client reference", async ({ page }) => {
  const problems = [];
  await collectPortalProblems(page, problems);

  const loginResponse = await page.context().request.post(`${baseURL}/api/method/login`, {
    form: { usr: clientUser, pwd: clientPassword },
  });
  expect(loginResponse.ok()).toBeTruthy();

  await page.goto(`${baseURL}/client/shipment-request/new`);
  await page.waitForLoadState("networkidle");

  const referenceInput = page
    .locator('input[data-fieldname="external_reference"], input[name="external_reference"], [data-fieldname="external_reference"] input')
    .first();
  await expect(referenceInput).toBeVisible();
  await expect(referenceInput).toHaveValue(/^ALPHA-OUT-\d{8}-\d{3}$/, { timeout: 10000 });
  await expect(page.locator("#client-product-picker")).toBeVisible({ timeout: 10000 });
  await page.locator("#client-product-picker-search").fill("ALPHA-001");
  await expect(page.locator("#client-product-picker-results")).toContainText("ALPHA-001", { timeout: 10000 });

  expect(problems).toEqual([]);
});

test("client can create a product from portal web form", async ({ page }) => {
  const problems = [];
  await collectPortalProblems(page, problems);

  const loginResponse = await page.context().request.post(`${baseURL}/api/method/login`, {
    form: { usr: clientUser, pwd: clientPassword },
  });
  expect(loginResponse.ok()).toBeTruthy();

  const sku = `UI-PORTAL-${Date.now()}`;
  await page.goto(`${baseURL}/client/products/new`);
  await page.waitForLoadState("networkidle");

  await page
    .locator('[data-fieldname="client_sku"] input, input[name="client_sku"], input[data-fieldname="client_sku"]')
    .first()
    .fill(sku);
  await page
    .locator('[data-fieldname="product_name"] input, input[name="product_name"], input[data-fieldname="product_name"]')
    .first()
    .fill("Portal UI Test Product");

  const uomInput = page.locator('[data-fieldname="uom"] input, input[name="uom"], input[data-fieldname="uom"]').first();
  await expect(uomInput).toBeVisible();
  if (!(await uomInput.inputValue())) {
    await uomInput.fill("Nos");
  }

  await Promise.all([
    page.waitForURL((url) => url.pathname === "/client/products/list", { timeout: 15000 }),
    page.getByRole("button", { name: /save product|save/i }).first().click(),
  ]);
  await page.waitForLoadState("networkidle");
  const productRow = page.locator("tr", { hasText: sku }).first();
  await expect(productRow).toBeVisible({ timeout: 15000 });
  await expect(productRow).toContainText("Synced", { timeout: 15000 });
  await expect(productRow).toContainText(/ALPHA-UI-PORTAL/);

  expect(problems).toEqual([]);
});

test("client can log out from portal", async ({ page, context }) => {
  const loginResponse = await page.context().request.post(`${baseURL}/api/method/login`, {
    form: { usr: clientUser, pwd: clientPassword },
  });
  expect(loginResponse.ok()).toBeTruthy();

  await page.goto(`${baseURL}/client/products/list`);
  await page.waitForLoadState("networkidle");

  await expect(page.locator("#three-pl-client-logout")).toBeVisible({ timeout: 10000 });
  await page.locator("#three-pl-client-logout").click();
  await page.waitForURL((url) => url.pathname === "/login", { timeout: 15000 });

  const sidCookie = (await context.cookies(baseURL)).find((cookie) => cookie.name === "sid");
  expect(sidCookie?.value === "Guest" || !sidCookie).toBeTruthy();

  await page.goto(`${baseURL}/client/products/list`);
  await page.waitForLoadState("networkidle");
  await expect(page.locator("body")).toContainText(/login|not permitted/i);
});
