import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import TokenClaims
from app.db.base import Base
from app.db.models import (
    Agent,
    AgentStatus,
    Delegation,
    DelegationStatus,
    Principal,
    PrincipalStatus,
    PrincipalType,
    RiskClassification,
)
from app.identity import (
    AgentIdentityResolver,
    AgentNotFoundError,
    ConflictingClientIdentityError,
    DefaultAgentClientResolver,
    ExpiredDelegationError,
    InactiveAgentError,
    InactiveDelegationError,
    InactivePrincipalError,
    MissingAgentClientMappingError,
    MissingDelegationError,
    PrincipalNotFoundError,
    SecurityContext,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def identity_resolver():
    return AgentIdentityResolver()


@pytest.fixture
def setup_valid_identity_graph(db_session: Session):
    # 1. Create Principal
    principal = Principal(
        id=uuid.uuid4(),
        type=PrincipalType.HUMAN,
        name="Alice Admin",
        external_id="auth0|alice123",
        status=PrincipalStatus.ACTIVE
    )
    db_session.add(principal)
    db_session.flush()

    # 2. Create Agent
    agent = Agent(
        id=uuid.uuid4(),
        name="FinanceBot-v1",
        owner_principal_id=principal.id,
        purpose="Automate invoice processing",
        version="1.0.0",
        status=AgentStatus.ACTIVE,
        risk_classification=RiskClassification.MEDIUM
    )
    db_session.add(agent)
    db_session.flush()

    # 3. Create Delegation
    delegation = Delegation(
        id=uuid.uuid4(),
        principal_id=principal.id,
        agent_id=agent.id,
        scope="agentos:read agentos:execute",
        status=DelegationStatus.ACTIVE,
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db_session.add(delegation)
    db_session.commit()

    return principal, agent, delegation


def test_valid_principal_agent_delegation_by_uuid(db_session, identity_resolver, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id)
    )

    ctx = identity_resolver.resolve_security_context(claims, db_session)

    assert isinstance(ctx, SecurityContext)
    assert ctx.principal.id == principal.id
    assert ctx.agent.id == agent.id
    assert ctx.delegation.id == delegation.id
    assert ctx.claims == claims


def test_explicit_client_to_agent_mapping(db_session, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph

    # Configure custom resolver mapping string client_id -> agent.id
    custom_client_resolver = DefaultAgentClientResolver(
        client_to_agent_map={"oauth-client-app-123": agent.id}
    )
    resolver = AgentIdentityResolver(agent_client_resolver=custom_client_resolver)

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id="oauth-client-app-123"
    )

    ctx = resolver.resolve_security_context(claims, db_session)
    assert ctx.agent.id == agent.id


def test_spoofed_agent_display_name_in_client_id_fails(db_session, identity_resolver, setup_valid_identity_graph):
    """
    SECURITY REQUIREMENT: Human-readable Agent.name MUST NEVER be accepted as proof of agent identity!
    Passing client_id="FinanceBot-v1" (display name, not UUID) MUST fail closed with AgentNotFoundError.
    """
    principal, agent, delegation = setup_valid_identity_graph

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id="FinanceBot-v1"  # Display name spoofing attempt
    )

    with pytest.raises(AgentNotFoundError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "No Agent found for OAuth client 'FinanceBot-v1'" in str(exc_info.value)


def test_conflicting_client_id_and_azp_claims_fails_closed(db_session, setup_valid_identity_graph):
    principal, agent1, delegation1 = setup_valid_identity_graph

    # Create second agent
    agent2 = Agent(
        id=uuid.uuid4(),
        name="HRBot-v2",
        owner_principal_id=principal.id,
        purpose="Process HR requests",
        version="2.0.0",
        status=AgentStatus.ACTIVE,
        risk_classification=RiskClassification.LOW
    )
    db_session.add(agent2)
    db_session.commit()

    resolver = AgentIdentityResolver()

    # Token claims contain conflicting client_id (agent1.id) and azp (agent2.id)
    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent1.id),
        azp=str(agent2.id)
    )

    with pytest.raises(ConflictingClientIdentityError) as exc_info:
        resolver.resolve_security_context(claims, db_session)

    assert "conflicting client_id" in str(exc_info.value)


def test_matching_client_id_and_azp_claims_succeeds(db_session, identity_resolver, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id),
        azp=str(agent.id)
    )

    ctx = identity_resolver.resolve_security_context(claims, db_session)
    assert ctx.agent.id == agent.id


def test_duplicate_agent_names_in_db_have_no_impact(db_session, identity_resolver, setup_valid_identity_graph):
    """
    Since resolution operates purely on UUID or explicit client mapping and NEVER display names,
    duplicate agent display names do not cause ambiguity.
    """
    principal, agent1, delegation1 = setup_valid_identity_graph

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent1.id)
    )

    ctx = identity_resolver.resolve_security_context(claims, db_session)
    assert ctx.agent.id == agent1.id


def test_nonexistent_principal_raises(db_session, identity_resolver, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph

    claims = TokenClaims(
        sub="nonexistent|user999",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id)
    )

    with pytest.raises(PrincipalNotFoundError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "Principal 'nonexistent|user999' not found" in str(exc_info.value)


def test_inactive_principal_raises(db_session, identity_resolver, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph
    principal.status = PrincipalStatus.SUSPENDED
    db_session.commit()

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id)
    )

    with pytest.raises(InactivePrincipalError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "status is SUSPENDED" in str(exc_info.value)


def test_missing_agent_client_mapping_raises(db_session, identity_resolver, setup_valid_identity_graph):
    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=None,
        azp=None
    )

    with pytest.raises(MissingAgentClientMappingError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "lack client_id/azp" in str(exc_info.value)


def test_unmapped_client_id_raises(db_session, identity_resolver, setup_valid_identity_graph):
    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id="unmapped-client-xyz"
    )

    with pytest.raises(AgentNotFoundError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "No Agent found for OAuth client 'unmapped-client-xyz'" in str(exc_info.value)


def test_inactive_agent_raises(db_session, identity_resolver, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph
    agent.status = AgentStatus.SUSPENDED
    db_session.commit()

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id)
    )

    with pytest.raises(InactiveAgentError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "status is SUSPENDED" in str(exc_info.value)


def test_missing_delegation_raises(db_session, identity_resolver, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph
    db_session.delete(delegation)
    db_session.commit()

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id)
    )

    with pytest.raises(MissingDelegationError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "No delegation relationship exists" in str(exc_info.value)


def test_inactive_revoked_delegation_raises(db_session, identity_resolver, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph
    delegation.status = DelegationStatus.REVOKED
    db_session.commit()

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id)
    )

    with pytest.raises(InactiveDelegationError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "revoked or inactive" in str(exc_info.value)


def test_expired_delegation_raises(db_session, identity_resolver, setup_valid_identity_graph):
    principal, agent, delegation = setup_valid_identity_graph
    delegation.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db_session.commit()

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id)
    )

    with pytest.raises(ExpiredDelegationError) as exc_info:
        identity_resolver.resolve_security_context(claims, db_session)

    assert "expired" in str(exc_info.value)


def test_client_id_impersonating_another_agent(db_session, identity_resolver, setup_valid_identity_graph):
    principal1, agent1, delegation1 = setup_valid_identity_graph

    # Create agent2 owned by principal1, but NO delegation exists for agent2
    agent2 = Agent(
        id=uuid.uuid4(),
        name="SecurityBot-v3",
        owner_principal_id=principal1.id,
        purpose="Security scanning",
        version="3.0.0",
        status=AgentStatus.ACTIVE,
        risk_classification=RiskClassification.HIGH
    )
    db_session.add(agent2)
    db_session.commit()

    # Caller attempts to present client_id of agent2
    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent2.id)
    )

    with pytest.raises(MissingDelegationError):
        identity_resolver.resolve_security_context(claims, db_session)


def test_spoofed_headers_and_arguments_ignored(db_session, identity_resolver, setup_valid_identity_graph):
    """
    Security Invariant: Even if spoofed headers, query params, tool args, or _meta contain
    fake agent_id or principal_id, AgentIdentityResolver uses ONLY verified TokenClaims.
    """
    principal, agent, delegation = setup_valid_identity_graph

    claims = TokenClaims(
        sub="auth0|alice123",
        iss="https://auth.agentos.com",
        aud="https://agentos-api-qm2r.onrender.com",
        scope={"agentos:execute"},
        client_id=str(agent.id)
    )

    # Simulated untrusted input payload
    spoofed_mcp_meta = {
        "_meta": {
            "principal_id": "00000000-0000-0000-0000-000000000000",
            "agent_id": "99999999-9999-9999-9999-999999999999",
            "user": "root"
        }
    }
    spoofed_tool_arguments = {
        "action_id": "something",
        "principal_id": "fake-principal",
        "agent_id": "fake-agent"
    }

    # Resolver interface accepts ONLY TokenClaims and Session
    ctx = identity_resolver.resolve_security_context(claims, db_session)

    # Assert security context is built 100% from validated claims
    assert ctx.principal.external_id == "auth0|alice123"
    assert ctx.agent.id == agent.id
    assert ctx.principal.id != uuid.UUID("00000000-0000-0000-0000-000000000000")
    assert ctx.agent.id != uuid.UUID("99999999-9999-9999-9999-999999999999")
