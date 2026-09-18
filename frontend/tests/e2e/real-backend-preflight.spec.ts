import { expect, test } from "@playwright/test";

test("preflight displays a real policy decision from the seeded sandbox API", async ({ page }) => {
  await page.addInitScript(() => {
    window.__AGENTOS_API_BASE_URL__ = "http://127.0.0.1:8100";
  });
  await page.goto("/policy-evaluation");

  const agent = page.locator("label").filter({ hasText: /^Agent/ }).locator("select");
  const action = page.locator("label").filter({ hasText: /^Action/ }).locator("select");
  const resource = page.locator("label").filter({ hasText: /^Resource/ }).locator("select");

  await expect(agent).toHaveValue(/.+/);
  await agent.selectOption({ label: "FinanceAgent" });
  await action.selectOption({ label: "bank_transfer" });
  await resource.selectOption({ label: "bank_account_001" });
  await page.getByRole("button", { name: "Refresh safe preview" }).click();

  await expect(page.getByText("Decision preview", { exact: true })).toBeVisible();
  await expect(page.getByText("REQUIRE_APPROVAL", { exact: true })).toBeVisible();
  await expect(page.getByText("Human approval and revalidation", { exact: true })).toBeVisible();
  await expect(page.getByText(/sandbox\/test-mode only/i)).toBeVisible();
});
