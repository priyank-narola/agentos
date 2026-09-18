import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page, type Route } from "@playwright/test";

// The local demo can use a dedicated AgentOS port when another project owns
// localhost:8000. Keep mock coverage independent of that developer setting.
const apiOrigins = ["http://localhost:8000", "http://127.0.0.1:8100"];
const now = "2026-09-18T09:00:00.000Z";

const agent = { id: "agent-1", name: "Billing guard", owner_principal_id: "requester-1", purpose: "Proposes governed billing actions", version: "1.0.0", status: "ACTIVE", risk_classification: "HIGH" };
const action = { id: "action-1", tool_id: "tool-1", name: "issue_credit", description: "Issue a customer credit", risk_level: "HIGH", status: "ACTIVE" };
const resource = { id: "resource-1", resource_type: "customer_account", resource_key: "customer-123", sensitivity: "HIGH", status: "ACTIVE" };
const request = {
  id: "request-1", tenant_id: "tenant-1", agent_id: agent.id, agent_name: agent.name,
  principal_id: "requester-1", principal_name: "Priya Requester", action_id: action.id,
  action_name: action.name, tool_id: "tool-1", tool_name: "Sandbox billing connector",
  resource_id: resource.id, resource_type: resource.resource_type, resource_key: resource.resource_key,
  parameters: { amount: 25, currency: "USD" }, status: "APPROVAL_PENDING", idempotency_key: "request-1-key",
  requested_at: now, decision: "REQUIRE_APPROVAL", reason: "High-risk action requires a distinct approver.",
  reason_code: "APPROVAL_REQUIRED", risk_level: "HIGH", risk_score: 80, risk_classification: "CRITICAL",
  risk_factors: [{ code: "HIGH_VALUE", contribution: 80, explanation: "The request crosses the sandbox review threshold." }],
  risk_engine_version: "deterministic-v1", execution_status: "NOT_EXECUTED",
  execution_receipt: { status: "NOT_EXECUTED", evidence_status: "NOT_RECORDED", recovery_status: "NOT_STARTED" }, decided_at: now,
};

const pendingApproval = {
  id: "approval-1", action_request_id: request.id, agent_id: agent.id, agent_name: agent.name,
  principal_id: request.principal_id, principal_name: request.principal_name, action_id: action.id,
  action_name: action.name, tool_id: request.tool_id, tool_name: request.tool_name,
  resource_id: resource.id, resource_type: resource.resource_type, resource_key: resource.resource_key,
  parameters: request.parameters, status: "PENDING", requested_by: request.principal_id,
  reason: "High-risk action requires a distinct approver.", risk_score: 80, risk_classification: "CRITICAL",
  risk_factors: request.risk_factors, policy_id: "policy-1", policy_version: 1,
  execution_status: "NOT_EXECUTED", execution_receipt: request.execution_receipt,
  requested_at: now, expires_at: "2026-09-19T09:00:00.000Z",
};

const preflight = {
  decision: "REQUIRE_APPROVAL", reason_code: "APPROVAL_REQUIRED", reason: "A distinct human review is required.",
  risk_level: "HIGH", risk_score: 80, risk_classification: "CRITICAL", approval_required: true,
  risk_factors: request.risk_factors, risk_engine_version: "deterministic-v1",
  matched_policies: [{ policy_id: "policy-1", policy_name: "Credit control", policy_version: 1, policy_priority: 1, rule_id: "rule-1", rule_effect: "ALLOW", rule_priority: 1 }],
  connector_provider: "SandboxBillingProvider", execution_plan: "HUMAN_APPROVAL_AND_REVALIDATION_REQUIRED",
  payload_digest: "sha256-test-digest", evaluated_at: now, warnings: ["Sandbox/test-mode connector only."],
};

async function routeApi(page: Page, onApprove?: (body: unknown) => void) {
  let decidedApproval: Record<string, unknown> | null = null;
  const handler = async (route: Route) => {
    const path = new URL(route.request().url()).pathname;
    const method = route.request().method();
    const json = (body: unknown) => route.fulfill({ contentType: "application/json", body: JSON.stringify(body) });
    if (path === "/api/v1/auth/me") return json({ authenticated: false });
    if (path === "/api/v1/agents") return json([agent]);
    if (path === "/api/v1/resources") return json([resource]);
    if (path === "/api/v1/tools") return json([{ id: "tool-1", name: "Sandbox billing connector", description: "Sandbox only", status: "ACTIVE" }]);
    if (path === "/api/v1/tools/tool-1/actions") return json([action]);
    if (path === "/api/v1/action-preflight" && method === "POST") return json(preflight);
    if (path === "/api/v1/approvals/approval-1/approvers") return json({ approval_id: "approval-1", approvers: [{ id: "approver-1", name: "Alex Approver", external_id: "alex", type: "HUMAN" }] });
    if (path === "/api/v1/principals") return json([
      { id: "requester-1", name: "Priya Requester", external_id: "priya", type: "HUMAN", status: "ACTIVE", created_at: now, updated_at: now },
      { id: "approver-1", name: "Alex Approver", external_id: "alex", type: "HUMAN", status: "ACTIVE", created_at: now, updated_at: now },
    ]);
    if (path === "/api/v1/approvals/approval-1/approve" && method === "POST") {
      const body = route.request().postDataJSON();
      onApprove?.(body);
      decidedApproval = { ...pendingApproval, status: "APPROVED", decision_reason: body.decision_reason, decided_by: body.approver_principal_id, decided_at: now, execution_status: "EXECUTED" };
      return json(decidedApproval);
    }
    if (path === "/api/v1/approvals/approval-1") return json(decidedApproval ?? pendingApproval);
    if (path === "/api/v1/approvals") return json(decidedApproval ? [decidedApproval] : [pendingApproval]);
    if (path === "/api/v1/action-requests/request-1") return json({ ...request, execution_status: decidedApproval ? "EXECUTED" : "NOT_EXECUTED" });
    return route.fulfill({ status: 404, contentType: "application/json", body: JSON.stringify({ detail: `Unhandled test API route: ${path}` }) });
  };
  await Promise.all(apiOrigins.map((origin) => page.route(`${origin}/api/v1/**`, handler)));
}

test("preflight renders a keyboard-accessible, non-persistent governed decision preview", async ({ page }) => {
  await routeApi(page);
  await page.goto("/policy-evaluation");
  await expect(page.getByRole("heading", { name: "Action preflight" })).toBeVisible();
  await expect(page.getByText("REQUIRE_APPROVAL", { exact: true })).toBeVisible();
  await expect(page.getByText("Sandbox/test-mode only")).toBeVisible();

  await page.getByLabel("Executable parameters JSON").focus();
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.type('{"amount":25,"currency":"USD"}');
  await expect(page.getByRole("button", { name: "Refresh safe preview" })).toBeEnabled();

  const results = await new AxeBuilder({ page }).include("main").analyze();
  expect(results.violations).toEqual([]);
});

test("approval cannot proceed without a reason and records the submitted reason", async ({ page }) => {
  let submitted: unknown;
  await routeApi(page, (body) => { submitted = body; });
  await page.goto("/approvals/approval-1");
  const approve = page.getByRole("button", { name: "Approve as Alex Approver" });
  await expect(approve).toBeDisabled();

  await page.getByLabel(/Decision reason required/i).fill("The customer-impact evidence and policy conditions have been reviewed.");
  await expect(approve).toBeEnabled();
  await approve.click();

  await expect(page.getByRole("heading", { name: "Approval decided" })).toBeVisible();
  await expect(page.locator("section").filter({ hasText: "Recorded decision reason:" })).toContainText("customer-impact evidence");
  expect(submitted).toEqual({ approver_principal_id: "approver-1", decision_reason: "The customer-impact evidence and policy conditions have been reviewed." });
});
