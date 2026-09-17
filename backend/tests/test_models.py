from uuid import uuid4

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import (
    Action,
    ActionRequest,
    Agent,
    AgentStatus,
    Decision,
    DecisionType,
    Delegation,
    Policy,
    PolicyRule,
    Principal,
    PrincipalStatus,
    PrincipalType,
    Resource,
    ResourceSensitivity,
    ResourceStatus,
    RiskClassification,
    Tool,
    DEFAULT_TENANT_ID,
)
from app.schemas import ActionRequestSchema, AgentSchema, DecisionSchema


engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)


def test_all_domain_tables_are_registered() -> None:
    table_names = set(inspect(engine).get_table_names())
    assert table_names == {
            "tenants",
            "principals",
            "principal_roles",
            "agents",
        "delegations",
        "tools",
        "actions",
        "resources",
        "policies",
        "policy_rules",
        "action_requests",
        "decisions",
        "approval_requests",
        "audit_events",
        "financial_executions",
        "reconciliation_jobs",
        "webhook_events",
    }



def test_security_relevant_constraints_are_declared() -> None:
    inspector = inspect(engine)
    assert {item["name"] for item in inspector.get_unique_constraints("actions")} == {"uq_actions_tool_name"}
    assert any(foreign_key["referred_table"] == "action_requests" for foreign_key in inspector.get_foreign_keys("decisions"))
    assert any(foreign_key["referred_table"] == "principals" for foreign_key in inspector.get_foreign_keys("delegations"))
    assert any(column["name"] == "idempotency_key" and column["nullable"] is False for column in inspector.get_columns("action_requests"))


def test_action_request_preserves_identity_and_target_relationships() -> None:
    with Session(engine) as session:
        principal = Principal(type=PrincipalType.HUMAN, name="Priyank", external_id="student-001", status=PrincipalStatus.ACTIVE)
        agent = Agent(name="FinanceAgent", owner=principal, purpose="Finance operations", version="1.0.0", status=AgentStatus.ACTIVE, risk_classification=RiskClassification.HIGH)
        delegation = Delegation(principal=principal, agent=agent, scope="finance.transfer")
        tool = Tool(name="Payments", description="Payment operations")
        action = Action(tool=tool, name="bank_transfer", description="Transfer funds", risk_level=RiskClassification.HIGH)
        resource = Resource(resource_type="bank_account", resource_key="bank_account_001", sensitivity=ResourceSensitivity.HIGH, status=ResourceStatus.ACTIVE)
        request = ActionRequest(agent=agent, principal=principal, action=action, resource=resource, parameters={"amount": 18000, "currency": "USD"}, idempotency_key="demo-transfer-001")
        session.add_all([delegation, request])
        session.commit()
        session.refresh(request)

        assert request.agent.name == "FinanceAgent"
        assert request.principal.external_id == "student-001"
        assert request.action.name == "bank_transfer"
        assert request.resource.resource_key == "bank_account_001"
        assert request.idempotency_key == "demo-transfer-001"
        assert delegation.agent is agent


def test_decision_and_policy_rule_trace_to_parent_records() -> None:
    with Session(engine) as session:
        principal = Principal(type=PrincipalType.HUMAN, name="Priyank", external_id=f"student-{uuid4()}", status=PrincipalStatus.ACTIVE)
        agent = Agent(name=f"ResearchAgent-{uuid4()}", owner=principal, purpose="Research", version="1.0.0", risk_classification=RiskClassification.MEDIUM)
        tool = Tool(name=f"Data-{uuid4()}", description="Data access")
        action = Action(tool=tool, name="read_data", description="Read data", risk_level=RiskClassification.MEDIUM)
        resource = Resource(resource_type="dataset", resource_key=f"dataset-{uuid4()}", sensitivity=ResourceSensitivity.MEDIUM)
        policy = Policy(name=f"Restricted data-{uuid4()}", version=1)
        rule = PolicyRule(policy=policy, effect="DENY", action="read_data", resource_type="dataset", conditions={"sensitivity": "HIGH"})
        request = ActionRequest(agent=agent, principal=principal, action=action, resource=resource, parameters={}, idempotency_key=f"request-{uuid4()}")
        decision = Decision(action_request=request, tenant_id=DEFAULT_TENANT_ID, decision=DecisionType.BLOCK, reason="Restricted resource", policy=policy, policy_version=1, risk_score=80)
        session.add(decision)
        session.commit()

        assert decision.action_request is request
        assert decision.policy is policy
        assert rule.policy is policy


def test_public_schemas_are_separate_from_orm_models() -> None:
    assert ActionRequestSchema.model_config["from_attributes"] is True
    assert AgentSchema.model_config["from_attributes"] is True
    assert DecisionSchema.model_config["from_attributes"] is True
    assert ActionRequestSchema is not ActionRequest
