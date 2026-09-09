# FRIEND DEMO TEST GUIDE

You only need a browser. You do not need the code, Git, Python, Node, Docker, or a database.

## 1. Open this URL
Open the URL you were given (it looks like `http://192.168.x.x:3100` for same-network, or an `https://…` tunnel URL for remote). Use Chrome.

## 2. What AgentOS is
AI agents can request powerful actions — like moving money. AgentOS is the layer that decides whether an action is authorized, how risky it is, whether a human must approve it, whether it actually executed, and what evidence was recorded. This demo shows that with a fake $25,000 wire transfer. **No real money moves — everything runs in a sandbox.**

## 3. Click "Run Treasury Governance Demo"
On the Control Center, click **Run Treasury Governance Demo** (or go to the "Flagship demo" page). Read the short explainer, then click **Run Treasury Governance Demo** again.

## 4. What to observe
Watch the lifecycle on the left and the action panel on the right:
- Agent: **TreasuryBot-v1** requesting the wire.
- Acting for: **Alice Smith** (Treasury Manager).
- Authority: Alice delegated the `wire_transfer` scope to the agent.
- Policy decision and risk: **75 / CRITICAL**, with the reasons shown.
- Approval required: a high-value wire needs a **distinct human** to approve — never the requester.
- Approve as **Bob Jones** (VP Finance). Then watch: revalidation → sandbox execution → execution record → audit events → the green **ACTION GOVERNED** proof.
- Everything you see comes from the real backend — it is not mocked.

## 5. How to run a blocked scenario
Scroll to **"AgentOS blocks unsafe actions"**. Click any scenario and read the result and reason, e.g.:
- Unauthorized action → **BLOCKED** (not authorized under policy)
- Payload tampering → **BLOCKED** (approved payload was changed)
- Revoked delegation → **BLOCKED** (delegation was removed before execution)
- Cross-tenant → **BLOCKED** · Duplicate → **PREVENTED** · Provider timeout → **HANDLED SAFELY**

## 6. How to reset / re-run
In the demo, click **Reset & run again** (shown after an approval completes). This starts a fresh governed request. Repeating the demo is fine and controlled.

## 7. How to report a bug
Tell the founder:
1. What you clicked (screen + button).
2. What you expected.
3. What happened instead (exact wording/color).
4. Any error text you saw.
Include the browser (Chrome/Firefox/Safari) and whether it happened the first time or after a reset. Please do not share any credentials or the demo URL publicly.

## 8. Questions for independent feedback
Please answer honestly — there are no wrong answers:
1. In your own words, what does AgentOS do?
2. Did you understand WHY the wire needed a human approver?
3. Did you understand WHY the blocked scenarios were stopped?
4. What was confusing or unclear?
5. What would you want to know before trusting this for a real company?
6. Who in a company do you think would care most about this — and why?
7. Would you want to watch a real AI agent being governed this way? In what workflow?
8. Anything that looked broken, misleading, or fake?
