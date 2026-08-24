"""Idempotent development data for the registry demo."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Action,
    Agent,
    CapabilityStatus,
    Delegation,
    Principal,
    PrincipalStatus,
    PrincipalType,
    Resource,
    ResourceSensitivity,
    ResourceStatus,
    RiskClassification,
    Tool,
    Policy,
    PolicyEffect,
    PolicyRule,
    PolicyStatus,
)


def _first(session: Session, model, **filters):
    return session.scalar(select(model).filter_by(**filters))


def seed_demo(session: Session) -> dict[str, int]:
    principal = _first(session, Principal, type=PrincipalType.HUMAN, external_id="demo-admin")
    if principal is None:
        principal = Principal(name="Demo Admin", type=PrincipalType.HUMAN, external_id="demo-admin", status=PrincipalStatus.ACTIVE)
        session.add(principal)
        session.flush()

    agent_specs = {
        "FinanceAgent": ("Finance operations", "1.0.0", RiskClassification.HIGH),
        "SalesAgent": ("Customer relationship operations", "1.0.0", RiskClassification.MEDIUM),
        "ResearchAgent": ("Internal research operations", "1.0.0", RiskClassification.MEDIUM),
    }
    agents = {}
    for name, (purpose, version, risk) in agent_specs.items():
        agent = _first(session, Agent, name=name)
        if agent is None:
            agent = Agent(name=name, purpose=purpose, version=version, risk_classification=risk, owner=principal)
            session.add(agent)
            session.flush()
        agents[name] = agent

    tool_specs = {"Payments": "Payment operations", "CRM": "Customer relationship operations", "Email": "Outbound email operations", "Data": "Internal data operations"}
    tools = {}
    for name, description in tool_specs.items():
        tool = _first(session, Tool, name=name)
        if tool is None:
            tool = Tool(name=name, description=description, status=CapabilityStatus.ACTIVE)
            session.add(tool)
            session.flush()
        tools[name] = tool

    action_specs = {
        "Payments": [("bank_transfer", "Transfer funds", RiskClassification.HIGH), ("refund_payment", "Refund a payment", RiskClassification.HIGH)],
        "CRM": [("read_customer", "Read customer records", RiskClassification.LOW), ("update_customer", "Update customer records", RiskClassification.MEDIUM)],
        "Email": [("send_email", "Send an email", RiskClassification.MEDIUM)],
        "Data": [("read_sensitive_payroll", "Read sensitive payroll data", RiskClassification.HIGH)],
    }
    action_count = 0
    for tool_name, specs in action_specs.items():
        for name, description, risk in specs:
            if _first(session, Action, tool_id=tools[tool_name].id, name=name) is None:
                session.add(Action(tool=tools[tool_name], name=name, description=description, risk_level=risk, status=CapabilityStatus.ACTIVE))
                action_count += 1

    resource_specs = [("bank_account", "bank_account_001", ResourceSensitivity.HIGH), ("database", "crm_database", ResourceSensitivity.MEDIUM), ("dataset", "payroll_dataset", ResourceSensitivity.HIGH), ("crm_record", "customer_record_001", ResourceSensitivity.MEDIUM)]
    resource_count = 0
    for resource_type, resource_key, sensitivity in resource_specs:
        if _first(session, Resource, resource_type=resource_type, resource_key=resource_key) is None:
            session.add(Resource(resource_type=resource_type, resource_key=resource_key, sensitivity=sensitivity, status=ResourceStatus.ACTIVE))
            resource_count += 1

    delegation_specs = [("FinanceAgent", "payments.bank"), ("SalesAgent", "crm.read"), ("ResearchAgent", "data.read")]
    delegation_count = 0
    issued_at = datetime.now(timezone.utc)
    for agent_name, scope in delegation_specs:
        if session.scalar(select(Delegation).where(Delegation.principal_id == principal.id, Delegation.agent_id == agents[agent_name].id, Delegation.scope == scope)) is None:
            session.add(Delegation(principal=principal, agent=agents[agent_name], scope=scope, issued_at=issued_at))
            delegation_count += 1

    policy_specs = [
        ("Demo Safe CRM Read", "read_customer", "crm_record", PolicyEffect.ALLOW, None),
        ("Demo Blocked Payroll", "read_sensitive_payroll", "dataset", PolicyEffect.DENY, None),
        ("Demo Approval Transfer", "bank_transfer", "bank_account", PolicyEffect.ALLOW, None),
    ]
    policies_created = 0
    for name, action_name, resource_type, effect, conditions in policy_specs:
        policy = _first(session, Policy, name=name, version=1)
        if policy is None:
            policy = Policy(name=name, version=1, priority=10, status=PolicyStatus.ACTIVE, description="Deterministic competition demo policy")
            policy.rules = [PolicyRule(effect=effect, action=action_name, resource_type=resource_type, priority=10, conditions=conditions)]
            session.add(policy)
            policies_created += 1

    session.commit()
    return {"principals": 1, "agents": len(agents), "tools": len(tools), "actions_created": action_count, "resources_created": resource_count, "delegations_created": delegation_count, "policies_created": policies_created}


if __name__ == "__main__":
    from app.db.session import SessionLocal

    if SessionLocal is None:
        raise SystemExit("DATABASE_URL must be configured before seeding")
    with SessionLocal() as db:
        print(seed_demo(db))
