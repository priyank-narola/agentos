import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.scenarios import ScenarioEngine

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Base.metadata.create_all(engine)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    with TestingSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    with TestingSession() as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def db_session():
    with TestingSession() as session:
        yield session


def test_scenario_a_low_risk_auto_allowed(db_session):
    """Scenario A: Low-risk transaction -> Auto-allowed, sandbox succeeds."""
    engine_svc = ScenarioEngine(db_session)
    res = engine_svc.run_scenario_a_low_risk()
    assert res["final_outcome"] == "SUCCESS"
    assert res["approval_state"] == "NOT_REQUIRED"
    assert res["execution_state"] == "EXECUTION_SUCCEEDED"


def test_scenario_b_high_risk_approved(db_session):
    """Scenario B: High-risk transaction -> Requires approval, independent approver approves, TOCTOU passes."""
    engine_svc = ScenarioEngine(db_session)
    res = engine_svc.run_scenario_b_high_risk()
    assert res["final_outcome"] == "SUCCESS"
    assert res["approval_state"] == "APPROVED"
    assert res["execution_state"] == "EXECUTION_SUCCEEDED"


def test_scenario_c_unauthorized_policy_denied(db_session):
    """Scenario C: Unauthorized transaction -> Policy denies, execution never occurs."""
    engine_svc = ScenarioEngine(db_session)
    res = engine_svc.run_scenario_c_rejected()
    assert res["final_outcome"] == "BLOCKED_BY_POLICY"
    assert res["execution_state"] == "NOT_EXECUTED"


def test_scenario_d_payload_tampering_blocked(db_session):
    """Scenario D: Tampered payload -> SHA-256 digest mismatch detected, execution blocked."""
    engine_svc = ScenarioEngine(db_session)
    res = engine_svc.run_scenario_d_tampered()
    assert res["final_outcome"] == "TAMPER_BLOCKED"
    assert res["execution_state"] == "NOT_EXECUTED"


def test_scenario_e_revoked_delegation_toctou_blocked(db_session):
    """Scenario E: Revoked delegation -> TOCTOU revalidation fails closed."""
    engine_svc = ScenarioEngine(db_session)
    res = engine_svc.run_scenario_e_revoked_agent()
    assert res["final_outcome"] == "TOCTOU_BLOCKED"
    assert res["execution_state"] == "NOT_EXECUTED"


def test_scenario_f_cross_tenant_blocked(db_session):
    """Scenario F: Cross-tenant resource access attempt -> Fails closed, zero cross-tenant leakage."""
    engine_svc = ScenarioEngine(db_session)
    res = engine_svc.run_scenario_f_cross_tenant()
    assert res["final_outcome"] == "CROSS_TENANT_BLOCKED"


def test_scenario_g_provider_timeout_handled(db_session):
    """Scenario G: Provider failure & timeout -> State machine handles TIMEOUT safely."""
    engine_svc = ScenarioEngine(db_session)
    res = engine_svc.run_scenario_g_provider_failure()
    assert res["final_outcome"] == "SAFE_TIMEOUT_HANDLED"
    assert res["execution_state"] == "TIMEOUT"


def test_scenario_h_duplicate_execution_prevented(db_session):
    """Scenario H: Duplicate execution attempt -> Second attempt returns DUPLICATE status."""
    engine_svc = ScenarioEngine(db_session)
    res = engine_svc.run_scenario_h_duplicate()
    assert res["final_outcome"] == "DUPLICATE_PREVENTED"
    assert res["first_execution_state"] == "EXECUTION_SUCCEEDED"
    assert res["second_execution_state"] == "DUPLICATE"


def test_demo_scenarios_rest_api():
    """Verify demo REST API lists and executes scenarios deterministically."""
    # List scenarios
    res_list = client.get("/api/v1/demo/scenarios")
    assert res_list.status_code == 200
    assert res_list.json()["total_scenarios"] == 8

    # Run scenario A via API
    res_run_a = client.post("/api/v1/demo/scenarios/SCENARIO_A/run")
    assert res_run_a.status_code == 200
    assert res_run_a.json()["final_outcome"] == "SUCCESS"

    # Reject invalid scenario key
    res_bad = client.post("/api/v1/demo/scenarios/INVALID_SCENARIO/run")
    assert res_bad.status_code == 400


def test_demo_summary_and_audit_chain_rest_api():
    """Verify control plane summary and audit chain trace endpoints."""
    res_b = client.post("/api/v1/demo/scenarios/SCENARIO_B/run")
    assert res_b.status_code == 200
    scenario_b = res_b.json()

    # Query summary
    res_sum = client.get("/api/v1/demo/summary")
    assert res_sum.status_code == 200
    assert res_sum.json()["total_scenarios_available"] == 8

    # Query audit chain trace for scenario B request ID
    req_id = scenario_b["action_request_id"]
    res_trace = client.get(f"/api/v1/demo/audit-chain/{req_id}")
    assert res_trace.status_code == 200
    assert len(res_trace.json()["audit_chain_steps"]) == 12

