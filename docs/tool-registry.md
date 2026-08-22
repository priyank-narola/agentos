# Tool Registry

Tools group capabilities, while Actions represent individual operations. A tool being active never means all actions under it are authorized. Each action therefore has its own status and risk level.

Actions are unique within a tool. They are registered through `/tools/{tool_id}/actions` and can be updated through `/actions/{action_id}`. The Phase 3 UI shows tool inventory; runtime policy enforcement is deliberately deferred.
