import { expect, test, type APIRequestContext } from "@playwright/test";

const SANDBOX_API = "http://127.0.0.1:8100";

async function createPendingSandboxApproval(request: APIRequestContext) {
  const [agentsResponse, resourcesResponse, principalsResponse] = await Promise.all([
    request.get(`${SANDBOX_API}/api/v1/agents`),
    request.get(`${SANDBOX_API}/api/v1/resources`),
    request.get(`${SANDBOX_API}/api/v1/principals`),
  ]);
  expect(agentsResponse.ok()).toBeTruthy();
  expect(resourcesResponse.ok()).toBeTruthy();
  expect(principalsResponse.ok()).toBeTruthy();

  const agents = await agentsResponse.json() as Array<{ id: string; name: string; owner_principal_id: string }>;
  const resources = await resourcesResponse.json() as Array<{ id: string; resource_type: string; resource_key: string }>;
  const principals = await principalsResponse.json() as Array<{ id: string; external_id: string }>;
  const financeAgent = agents.find((agent) => agent.name === "FinanceAgent");
  const treasuryResource = resources.find((resource) => resource.resource_type === "account" && resource.resource_key === "ACC-DEMO-TREASURY-01");
  const requester = principals.find((principal) => principal.external_id === "demo-admin");
  expect(financeAgent).toBeTruthy();
  expect(treasuryResource).toBeTruthy();
  expect(requester).toBeTruthy();

  const toolsResponse = await request.get(`${SANDBOX_API}/api/v1/tools`);
  expect(toolsResponse.ok()).toBeTruthy();
  const tools = await toolsResponse.json() as Array<{ id: string; name: string }>;
  const payments = tools.find((tool) => tool.name === "Payments");
  expect(payments).toBeTruthy();
  const actionsResponse = await request.get(`${SANDBOX_API}/api/v1/tools/${payments!.id}/actions`);
  expect(actionsResponse.ok()).toBeTruthy();
  const actions = await actionsResponse.json() as Array<{ id: string; name: string }>;
  const wireTransfer = actions.find((action) => action.name === "wire_transfer");
  expect(wireTransfer).toBeTruthy();

  const gatewayResponse = await request.post(`${SANDBOX_API}/api/v1/action-requests`, {
    data: {
      principal_id: requester!.id,
      agent_id: financeAgent!.id,
      action_id: wireTransfer!.id,
      resource_id: treasuryResource!.id,
      parameters: {
        amount: "15400.00",
        currency: "USD",
        beneficiary_id: "BEN-PLAYWRIGHT-SANDBOX",
        source_account_id: "ACC-DEMO-TREASURY-01",
        destination_account_id: "ACC-PLAYWRIGHT-SANDBOX",
        transaction_reference: `PW-APPROVAL-${Date.now()}`,
        purpose: "Playwright sandbox-only approval verification",
      },
      idempotency_key: `playwright-approval-${Date.now()}`,
    },
  });
  expect(gatewayResponse.ok()).toBeTruthy();
  const gateway = await gatewayResponse.json() as { action_request_id: string; decision: string };
  expect(gateway.decision).toBe("REQUIRE_APPROVAL");

  const approvalsResponse = await request.get(`${SANDBOX_API}/api/v1/approvals`);
  expect(approvalsResponse.ok()).toBeTruthy();
  const approvals = await approvalsResponse.json() as Array<{ id: string; action_request_id: string; status: string }>;
  const approval = approvals.find((item) => item.action_request_id === gateway.action_request_id);
  expect(approval?.status).toBe("PENDING");
  return approval!.id;
}

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

test("approval workbench records an independent human decision against the real sandbox API", async ({ page, request }) => {
  const approvalId = await createPendingSandboxApproval(request);
  await page.addInitScript(() => {
    window.__AGENTOS_API_BASE_URL__ = "http://127.0.0.1:8100";
  });
  await page.goto(`/approvals/${approvalId}`);

  const approver = page.getByLabel("Approve as");
  const decisionReason = page.getByLabel(/Decision reason/i);
  const approve = page.getByRole("button", { name: /Approve as Dana Reviewer/ });

  await expect(approver).toHaveValue(/.+/);
  await expect(approver.locator("option")).not.toContainText("Demo Admin");
  await expect(approve).toBeDisabled();
  await decisionReason.fill("Verified the exact sandbox payload, policy route, risk context, and recovery posture.");
  await expect(approve).toBeEnabled();
  await approve.click();

  await expect(page.getByRole("heading", { name: "Approval decided" })).toBeVisible();
  await expect(page.getByText("Recorded decision reason:")).toBeVisible();
  await expect(page.getByText(/Verified the exact sandbox payload/)).toBeVisible();
  await expect(page.getByText(/Executed in the sandbox provider/)).toBeVisible();
});

test("policy workbench simulates a fresh draft without publishing or creating an action", async ({ page, request }) => {
  const actionsBefore = await request.get(`${SANDBOX_API}/api/v1/action-requests`);
  expect(actionsBefore.ok()).toBeTruthy();
  const actionCountBefore = (await actionsBefore.json() as unknown[]).length;

  const created = await request.post(`${SANDBOX_API}/api/v1/policies`, {
    data: {
      name: `Playwright draft ${Date.now()}`,
      description: "Sandbox-only draft policy simulation verification",
      version: 1,
      priority: 1,
    },
  });
  expect(created.ok()).toBeTruthy();
  const draft = await created.json() as { id: string; status: string };
  expect(draft.status).toBe("DRAFT");

  const createdRule = await request.post(`${SANDBOX_API}/api/v1/policies/${draft.id}/rules`, {
    data: { effect: "ALLOW", action: "wire_transfer", resource_type: "account", priority: 1 },
  });
  expect(createdRule.ok()).toBeTruthy();

  await page.addInitScript(() => {
    window.__AGENTOS_API_BASE_URL__ = "http://127.0.0.1:8100";
  });
  await page.goto(`/policies/${draft.id}`);

  const simulation = page.locator("section").filter({ hasText: "Draft-only simulation" });
  await expect(simulation.getByText("Test this draft without publishing")).toBeVisible();
  await simulation.locator("label").filter({ hasText: /^Agent/ }).locator("select").selectOption({ label: "FinanceAgent" });
  await simulation.locator("label").filter({ hasText: /^Action/ }).locator("select").selectOption({ label: "wire_transfer" });
  await simulation.locator("label").filter({ hasText: /^Resource/ }).locator("select").selectOption({ label: "ACC-DEMO-TREASURY-01" });
  await simulation.getByRole("button", { name: "Run draft simulation" }).click();

  await expect(simulation.getByText(/matching draft rule\(s\) · no policy status changed/i)).toBeVisible();
  const after = await request.get(`${SANDBOX_API}/api/v1/policies/${draft.id}`);
  expect(after.ok()).toBeTruthy();
  expect((await after.json() as { status: string }).status).toBe("DRAFT");
  const actionsAfter = await request.get(`${SANDBOX_API}/api/v1/action-requests`);
  expect((await actionsAfter.json() as unknown[]).length).toBe(actionCountBefore);
});
