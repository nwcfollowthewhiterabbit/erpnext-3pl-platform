const { test, expect } = require("@playwright/test");

const baseURL = process.env.CLIENT_PORTAL_BASE_URL || "https://erpnext.77.237.244.169.sslip.io";
const clientUser = process.env.CLIENT_PORTAL_USER || "alpha.client@example.test";
const clientPassword = process.env.CLIENT_PORTAL_PASSWORD || "AlphaClient2026!";

const portalPages = [
  "/client/receiving-notice",
  "/client/inventory",
  "/client/shipment-request",
  "/client/discrepancy-instruction",
];

const navLabels = ["Receiving Notices", "Inventory", "Shipment Requests", "Discrepancy Instructions"];

test("client portal pages render without permission errors", async ({ page }) => {
  const problems = [];

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
      if (url.includes("/desk/3pl-warehouse")) return;
      let body = "";
      try {
        body = (await response.text()).slice(0, 600);
      } catch {
        body = "<unreadable body>";
      }
      problems.push(`response ${response.status()} ${url}: ${body}`);
    }
  });

  const loginResponse = await page.context().request.post(`${baseURL}/api/method/login`, {
    form: { usr: clientUser, pwd: clientPassword },
  });
  expect(loginResponse.ok()).toBeTruthy();
  expect(await loginResponse.json()).toMatchObject({ message: "No App" });

  for (const path of portalPages) {
    await page.goto(`${baseURL}${path}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    const bodyText = await page.locator("body").innerText();
    if (/not permitted|no permission|page not found/i.test(bodyText)) {
      problems.push(`body ${path}: ${bodyText.slice(0, 800)}`);
    }

    for (const label of navLabels) {
      if (!(await page.getByRole("link", { name: label }).isVisible().catch(() => false))) {
        problems.push(`body ${path}: missing nav label ${label}`);
      }
    }
  }

  expect(problems).toEqual([]);
});
