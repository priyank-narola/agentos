import time
import math
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from app.auth import TokenValidator
from app.identity import AgentIdentityResolver
from app.risk.engine import RiskEngine, RiskContext
from app.db.models import Tool, Action, Resource
from app.services.policy import PolicyService
from app.schemas import PolicyEvaluationRequest




def percentile(data: list[float], p: float) -> float:
    """Calculate p-th percentile from list of floats."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1


class MCPPerformanceBenchmark:
    """
    Performance latency measurement engine for AgentOS MCP Streamable HTTP authorization stack.
    Measures token validation, identity resolution, policy evaluation, risk evaluation, and total authorization latency over N requests.
    """

    def __init__(self, db: Session, token_validator: TokenValidator | None = None) -> None:
        self.db = db
        self.token_validator = token_validator or TokenValidator()
        if not self.token_validator.secret_key:
            self.token_validator.secret_key = "test-mcp-secret-key-phase4a"
        self.identity_resolver = AgentIdentityResolver()
        self.policy_engine = PolicyService(db)
        self.risk_engine = RiskEngine()



    def run_benchmark(self, token: str, dummy_eval_req: PolicyEvaluationRequest, num_requests: int = 100) -> dict[str, Any]:
        token_val_latencies: list[float] = []
        identity_latencies: list[float] = []
        policy_latencies: list[float] = []
        risk_latencies: list[float] = []
        total_latencies: list[float] = []

        for _ in range(num_requests):
            t0 = time.perf_counter()

            # 1. Token validation
            tv0 = time.perf_counter()
            claims = self.token_validator.validate_token(token)
            tv1 = time.perf_counter()
            token_val_latencies.append((tv1 - tv0) * 1000.0)

            # 2. Identity resolution
            ir0 = time.perf_counter()
            sec_ctx = self.identity_resolver.resolve_security_context(claims, self.db)
            ir1 = time.perf_counter()
            identity_latencies.append((ir1 - ir0) * 1000.0)

            # 3. Policy evaluation
            pe0 = time.perf_counter()
            pol_res = self.policy_engine.evaluate(dummy_eval_req)
            pe1 = time.perf_counter()
            policy_latencies.append((pe1 - pe0) * 1000.0)

            # 4. Risk evaluation
            re0 = time.perf_counter()
            tool = self.db.get(Tool, dummy_eval_req.tool_id)
            action = self.db.get(Action, dummy_eval_req.action_id)
            resource = self.db.get(Resource, dummy_eval_req.resource_id)
            risk_ctx = RiskContext(
                agent=sec_ctx.agent,
                tool=tool,
                action=action,
                resource=resource,
                delegations=tuple(sec_ctx.agent.delegations),
                parameters=dummy_eval_req.parameters,
                evaluated_at=datetime.now(timezone.utc)
            )
            risk_res = self.risk_engine.evaluate(risk_ctx)
            re1 = time.perf_counter()
            risk_latencies.append((re1 - re0) * 1000.0)


            t1 = time.perf_counter()
            total_latencies.append((t1 - t0) * 1000.0)

        def summarize(latencies: list[float]) -> dict[str, float]:
            return {
                "p50_ms": round(percentile(latencies, 50), 3),
                "p95_ms": round(percentile(latencies, 95), 3),
                "p99_ms": round(percentile(latencies, 99), 3),
                "max_ms": round(max(latencies), 3),
            }

        return {
            "num_requests": num_requests,
            "metrics": {
                "token_validation_latency": summarize(token_val_latencies),
                "identity_resolution_latency": summarize(identity_latencies),
                "policy_evaluation_latency": summarize(policy_latencies),
                "risk_evaluation_latency": summarize(risk_latencies),
                "complete_mcp_authorization_latency": summarize(total_latencies),
            }
        }
