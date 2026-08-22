# Deterministic Policy Engine

Phase 4 adds a server-side, deterministic evaluator for hypothetical action requests. It evaluates existing principal, agent, delegation, tool, action, resource, and active policy records. It returns a decision and trace but never creates an `ActionRequest`, persists a `Decision`, or executes an action.

## Model and API

- `POST /api/v1/policies` creates a versioned policy container.
- `GET /api/v1/policies` and `GET /api/v1/policies/{id}` read policy containers and rules.
- `POST /api/v1/policies/{id}/rules` adds a rule to a policy.
- `POST /api/v1/policy-evaluations` evaluates a hypothetical request.

Rules match exact action and resource type. Supported deterministic conditions are:

- `resource_sensitivity`: exact sensitivity match
- `amount_lte`: numeric request parameter upper bound
- `context`: exact `policy_context.name` match

Unknown condition keys fail closed and do not match.

## Security boundary

The browser only submits evaluation inputs and renders the backend result. It cannot manufacture an authorization decision. Authentication and caller authorization are not implemented yet, so these endpoints are development/demo control-plane endpoints, not a production access boundary.
