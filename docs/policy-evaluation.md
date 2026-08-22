# Policy Evaluation

## Evaluation algorithm

The evaluator runs these steps in order:

1. Resolve principal, agent, tool, action, and resource IDs.
2. Validate that the principal owns the agent.
3. Require an active agent.
4. Require a matching delegation from that principal to that agent.
5. Require a non-revoked, non-expired delegation whose scope covers the normalized tool/action operation.
6. Require active tool, action, and resource records.
7. Resolve matching rules from active policies only.
8. Sort matches by policy priority, rule priority, policy ID, and rule ID.
9. Any explicit `DENY` takes precedence over every `ALLOW`, regardless of priority.
10. A matching allow for a `HIGH` risk action returns `REQUIRE_APPROVAL`.
11. No matching rule returns `DENY` with `DEFAULT_DENY`.
12. Return every completed check as an ordered trace step.

## Decisions and reason codes

The evaluation contract uses `ALLOW`, `DENY`, and `REQUIRE_APPROVAL`. The existing Phase 2 persistence enum uses `BLOCK`; no persistence decision is created in Phase 4.

Stable reason codes include:

- `INVALID_REFERENCE`
- `PRINCIPAL_AGENT_MISMATCH`
- `AGENT_INACTIVE`
- `DELEGATION_MISSING`
- `DELEGATION_INACTIVE`
- `DELEGATION_EXPIRED`
- `DELEGATION_SCOPE_MISMATCH`
- `TOOL_INACTIVE`
- `ACTION_INACTIVE`
- `RESOURCE_INACTIVE`
- `POLICY_DENY`
- `POLICY_ALLOW`
- `HIGH_RISK_APPROVAL`
- `DEFAULT_DENY`

## Examples

- Active agent + valid `crm.read` delegation + active low-risk action + matching allow: `ALLOW`.
- Same request with no matching policy: `DENY / DEFAULT_DENY`.
- Active high-risk `bank_transfer` with matching allow: `REQUIRE_APPROVAL`.
- Matching allow and deny policies: `DENY / POLICY_DENY`.
- Expired delegation: `DENY / DELEGATION_EXPIRED`.

## Limitations

Phase 4 does not create or execute runtime action requests, persist decisions, calculate a full risk score, implement human approval, authenticate callers, or integrate external policy engines such as OPA/Rego.
