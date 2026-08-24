from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.db.models import Action, Agent, CapabilityStatus, Delegation, DelegationStatus, Resource, ResourceSensitivity, ResourceStatus, RiskClassification, Tool
from app.risk import RiskContext, RiskEngine

NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def context(*, action_risk=RiskClassification.LOW, agent_risk=RiskClassification.LOW, sensitivity=ResourceSensitivity.LOW, amount=None):
    tool = Tool(id=uuid4(), name="RiskTool", description="Risk tool", status=CapabilityStatus.ACTIVE)
    action = Action(id=uuid4(), tool_id=tool.id, name="read_data", description="Read", risk_level=action_risk, status=CapabilityStatus.ACTIVE)
    agent = Agent(id=uuid4(), name=f"RiskAgent-{uuid4()}", owner_principal_id=uuid4(), purpose="Risk test", version="1", risk_classification=agent_risk)
    resource = Resource(id=uuid4(), resource_type="dataset", resource_key=str(uuid4()), sensitivity=sensitivity, status=ResourceStatus.ACTIVE)
    delegation = Delegation(id=uuid4(), principal_id=agent.owner_principal_id, agent_id=agent.id, scope="risktool.read", status=DelegationStatus.ACTIVE)
    parameters = {} if amount is None else {"amount": amount}
    return RiskContext(agent, tool, action, resource, (delegation,), parameters, NOW)


def test_risk_evaluation_is_deterministic_and_explainable() -> None:
    engine = RiskEngine()
    first = engine.evaluate(context(action_risk=RiskClassification.MEDIUM, sensitivity=ResourceSensitivity.MEDIUM))
    second = engine.evaluate(context(action_risk=RiskClassification.MEDIUM, sensitivity=ResourceSensitivity.MEDIUM))
    assert (first.score, first.classification, first.factors) == (second.score, second.classification, second.factors)
    assert sum(factor.contribution for factor in first.factors) == first.score
    assert all(factor.code and factor.explanation and factor.contribution > 0 for factor in first.factors)


@pytest.mark.parametrize(("kwargs", "score", "classification"), [
    ({}, 5, "LOW"),
    ({"action_risk": RiskClassification.MEDIUM, "agent_risk": RiskClassification.MEDIUM}, 25, "MEDIUM"),
    ({"action_risk": RiskClassification.HIGH, "sensitivity": ResourceSensitivity.HIGH}, 55, "HIGH"),
    ({"action_risk": RiskClassification.HIGH, "agent_risk": RiskClassification.HIGH, "sensitivity": ResourceSensitivity.HIGH, "amount": 15000}, 95, "CRITICAL"),
])
def test_known_risk_classifications(kwargs, score, classification) -> None:
    result = RiskEngine().evaluate(context(**kwargs))
    assert (result.score, result.classification) == (score, classification)


@pytest.mark.parametrize(("score", "classification"), [(24, "LOW"), (25, "MEDIUM"), (49, "MEDIUM"), (50, "HIGH"), (74, "HIGH"), (75, "CRITICAL"), (101, "CRITICAL"), (-1, "LOW")])
def test_classification_boundaries(score, classification) -> None:
    assert RiskEngine.classify(score) == classification


def test_score_is_bounded_and_engine_does_not_authorize() -> None:
    result = RiskEngine().evaluate(context(action_risk=RiskClassification.HIGH, agent_risk=RiskClassification.HIGH, sensitivity=ResourceSensitivity.HIGH, amount=10**12))
    assert 0 <= result.score <= 100
    assert not hasattr(result, "decision")
    assert not hasattr(result, "authorized")
