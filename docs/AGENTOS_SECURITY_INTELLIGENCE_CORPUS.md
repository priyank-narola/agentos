# AgentOS Security Intelligence Corpus — Schema & Governance

**Status:** FOUNDATION — schema only. No data collected or scraped today.
**Purpose:** a provenance-tagged corpus that will later feed risk intelligence, anomaly detection, policy reasoning, and security-evaluation assistance. **Models assist; deterministic policy remains the final authority.**

## Example schema (one governance case)
```
{
  "id": "<uuid>",
  "source": { "authoritative_url": "https://…", "kind": "public_report|incident|policy_doc|vendor_doc", "accessed": "YYYY-MM-DD", "provenance_note": "" },
  "agent": { "type": "llm_tool_use|autonomous|copilot|…", "role": "" },
  "principal": { "kind": "human|service|org", "role": "" },
  "intent": { "description": "", "confidence": null },
  "action": { "name": "", "tool": "", "arguments_summary": "" },
  "resource": { "type": "", "sensitivity": "LOW|MEDIUM|HIGH", "owner": "" },
  "authority": { "delegation": "", "scope": "", "authenticated_identity": "" },
  "policy": { "applicable": "", "effect": "ALLOW|DENY|REQUIRE_APPROVAL" },
  "context": { "risk_factors": [], "amount": null, "currency": null, "untrusted_input": false },
  "attack_type": "prompt_injection|tool_abuse|impersonation|escalation|exfiltration|policy_violation|financial_abuse|none",
  "expected_decision": "ALLOW|DENY|REQUIRE_APPROVAL",
  "actual_decision": null,
  "approval_required": false,
  "execution_outcome": "NOT_EXECUTED|SUCCEEDED|FAILED|TIMEOUT|UNKNOWN",
  "explanation": "",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "verified": false
}
```

## Corpus categories (initial)
agent authorization · IAM · OAuth/delegation · MCP security · tool-use security · prompt injection · privilege escalation · data exfiltration · malicious tools · agent impersonation · policy violations · financial controls · enterprise approval workflows · AI governance · AI security incidents

## Data policy
- Only authoritative/public sources (vendor/advisory/incident reports, standards, open frameworks).
- **No blind scraping.** Every entry retains provenance and source-kind.
- Entries are tagged `verified:false` until independently reviewed.
- **No customer data** is ever collected into this corpus.
