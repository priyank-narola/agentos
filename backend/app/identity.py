import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import AuthError, TokenClaims
from app.db.models import Agent, AgentStatus, Delegation, DelegationStatus, Principal, PrincipalStatus


class IdentityResolutionError(AuthError):
    """Base exception for identity and delegation resolution failures (HTTP 403 Forbidden)."""
    def __init__(self, message: str, status_code: int = 403, error_type: str = "identity_resolution_failed"):
        super().__init__(message, status_code=status_code)
        self.error_type = error_type


class PrincipalNotFoundError(IdentityResolutionError):
    """Raised when token.sub cannot be resolved to an existing Principal."""
    def __init__(self, message: str = "Principal not found"):
        super().__init__(message, status_code=403, error_type="principal_not_found")


class InactivePrincipalError(IdentityResolutionError):
    """Raised when resolved Principal status is not ACTIVE."""
    def __init__(self, message: str = "Principal is inactive or suspended"):
        super().__init__(message, status_code=403, error_type="inactive_principal")


class MissingAgentClientMappingError(IdentityResolutionError):
    """Raised when token claims lack a client_id/azp claim for agent resolution."""
    def __init__(self, message: str = "Missing OAuth client identifier for agent resolution"):
        super().__init__(message, status_code=403, error_type="missing_agent_client_mapping")


class ConflictingClientIdentityError(IdentityResolutionError):
    """Raised when client_id and azp claims point to conflicting agent identities."""
    def __init__(self, message: str = "Conflicting client_id and azp claims in token"):
        super().__init__(message, status_code=403, error_type="conflicting_client_identity")


class AgentNotFoundError(IdentityResolutionError):
    """Raised when OAuth client identifier cannot be resolved to an existing Agent."""
    def __init__(self, message: str = "Agent not found"):
        super().__init__(message, status_code=403, error_type="agent_not_found")


class InactiveAgentError(IdentityResolutionError):
    """Raised when resolved Agent status is not ACTIVE."""
    def __init__(self, message: str = "Agent is inactive or suspended"):
        super().__init__(message, status_code=403, error_type="inactive_agent")


class MissingDelegationError(IdentityResolutionError):
    """Raised when no delegation relationship exists between Principal and Agent."""
    def __init__(self, message: str = "No delegation relationship exists between principal and agent"):
        super().__init__(message, status_code=403, error_type="missing_delegation")


class InactiveDelegationError(IdentityResolutionError):
    """Raised when delegation relationship between Principal and Agent is revoked or inactive."""
    def __init__(self, message: str = "Delegation between principal and agent is inactive or revoked"):
        super().__init__(message, status_code=403, error_type="inactive_delegation")


class ExpiredDelegationError(IdentityResolutionError):
    """Raised when delegation relationship between Principal and Agent has expired."""
    def __init__(self, message: str = "Delegation between principal and agent has expired"):
        super().__init__(message, status_code=403, error_type="expired_delegation")


@dataclass(frozen=True)
class SecurityContext:
    """Trusted, immutable security context linking Principal, Agent, and active Delegation."""
    principal: Principal
    agent: Agent
    delegation: Delegation
    claims: TokenClaims
    resolved_at: datetime


class AgentClientResolver(ABC):
    """Abstract strategy interface for resolving OAuth client identity to an AgentOS Agent record."""

    @abstractmethod
    def resolve_agent(self, client_id: Optional[str], db: Session, azp: Optional[str] = None) -> Agent | None:
        """
        Map validated client_id / azp claims to Agent entity.
        MUST NOT rely on display Agent.name as proof of identity.
        """
        pass


class DefaultAgentClientResolver(AgentClientResolver):
    """
    Default AgentClientResolver for AgentOS.
    Maps OAuth client_id / azp to Agent entity using:
    1. Explicit client_to_agent_map dictionary (mapping external client_id string -> Agent.id UUID).
    2. Direct UUID lookup if client_id / azp is formatted as a valid Agent.id UUID string.

    SECURITY GUARANTEE: Human-readable Agent.name is NEVER used for identity matching.
    Conflicting client_id and azp claims raise ConflictingClientIdentityError (fail closed).
    """

    def __init__(self, client_to_agent_map: Optional[dict[str, Union[uuid.UUID, str]]] = None):
        self._map: dict[str, uuid.UUID] = {}
        if client_to_agent_map:
            for key, val in client_to_agent_map.items():
                if isinstance(val, str):
                    self._map[key.strip()] = uuid.UUID(val.strip())
                else:
                    self._map[key.strip()] = val

    def resolve_agent(self, client_id: Optional[str], db: Session, azp: Optional[str] = None) -> Agent | None:
        c1 = client_id.strip() if client_id else None
        c2 = azp.strip() if azp else None

        if not c1 and not c2:
            return None

        # Resolve primary client_id and azp independently if both present
        agent1 = self._resolve_single_client(c1, db) if c1 else None
        agent2 = self._resolve_single_client(c2, db) if c2 else None

        if c1 and c2 and c1 != c2:
            if agent1 and agent2 and agent1.id != agent2.id:
                raise ConflictingClientIdentityError(
                    f"Token contains conflicting client_id '{c1}' (Agent {agent1.id}) and azp '{c2}' (Agent {agent2.id})"
                )

        return agent1 or agent2

    def _resolve_single_client(self, client_str: str, db: Session) -> Agent | None:
        # 1. Check explicit client_to_agent_map
        if client_str in self._map:
            agent_uuid = self._map[client_str]
            return db.scalar(select(Agent).where(Agent.id == agent_uuid))

        # 2. Try parsing as Agent.id UUID directly
        try:
            agent_uuid = uuid.UUID(client_str)
            return db.scalar(select(Agent).where(Agent.id == agent_uuid))
        except ValueError:
            pass

        # 3. SECURITY: Explicitly DO NOT match on Agent.name!
        return None


class AgentIdentityResolver:
    """
    Transport-independent Principal / Agent / Delegation Identity Resolver.
    Converts cryptographically validated TokenClaims + SQLAlchemy Session into a trusted SecurityContext.
    Identity is derived STRICTLY from verified token claims. Client-supplied headers, params,
    tool arguments, or MCP _meta values are NEVER trusted or accepted for identity.
    """

    def __init__(self, agent_client_resolver: Optional[AgentClientResolver] = None):
        self.agent_client_resolver = agent_client_resolver or DefaultAgentClientResolver()

    def resolve_security_context(self, claims: TokenClaims, db: Session) -> SecurityContext:
        """
        Resolve Principal, Agent, and active Delegation strictly from token claims.
        Fails closed on any missing, inactive, or expired relationship.
        """
        if not claims or not claims.sub or not claims.sub.strip():
            raise PrincipalNotFoundError("Missing or empty subject claim in token")

        # 1. Principal Resolution
        principal = self._resolve_principal(claims.sub, db)
        if not principal:
            raise PrincipalNotFoundError(f"Principal '{claims.sub}' not found")

        if principal.status != PrincipalStatus.ACTIVE:
            raise InactivePrincipalError(f"Principal '{principal.id}' status is {principal.status.value}")

        # 2. Agent Resolution (via OAuth client_id / azp)
        client_id = claims.client_id
        azp = claims.azp

        if not client_id and not azp:
            raise MissingAgentClientMappingError("Token claims lack client_id/azp for agent resolution")

        agent = self.agent_client_resolver.resolve_agent(client_id=client_id, db=db, azp=azp)
        if not agent:
            raise AgentNotFoundError(f"No Agent found for OAuth client '{client_id or azp}'")

        if agent.status != AgentStatus.ACTIVE:
            raise InactiveAgentError(f"Agent '{agent.id}' status is {agent.status.value}")

        # 3. Delegation Validation
        delegation = self._resolve_delegation(principal.id, agent.id, db)

        return SecurityContext(
            principal=principal,
            agent=agent,
            delegation=delegation,
            claims=claims,
            resolved_at=datetime.now(timezone.utc)
        )

    def _resolve_principal(self, sub: str, db: Session) -> Principal | None:
        sub_str = sub.strip()
        # Query by external_id first
        principal = db.scalar(select(Principal).where(Principal.external_id == sub_str))
        if principal:
            return principal

        # Try matching by UUID id
        try:
            p_uuid = uuid.UUID(sub_str)
            principal = db.scalar(select(Principal).where(Principal.id == p_uuid))
            if principal:
                return principal
        except ValueError:
            pass

        return None

    def _resolve_delegation(self, principal_id: uuid.UUID, agent_id: uuid.UUID, db: Session) -> Delegation:
        stmt = (
            select(Delegation)
            .where(
                Delegation.principal_id == principal_id,
                Delegation.agent_id == agent_id,
            )
            .order_by(Delegation.issued_at.desc())
        )
        delegations = list(db.scalars(stmt).all())
        if not delegations:
            raise MissingDelegationError(
                f"No delegation relationship exists between Principal '{principal_id}' and Agent '{agent_id}'"
            )

        # Find active delegation
        active_delegation = None
        for d in delegations:
            if d.status == DelegationStatus.ACTIVE:
                active_delegation = d
                break

        if not active_delegation:
            raise InactiveDelegationError(
                f"Delegation relationship between Principal '{principal_id}' and Agent '{agent_id}' is revoked or inactive"
            )

        # Expiration check
        if active_delegation.expires_at is not None:
            now_utc = datetime.now(timezone.utc)
            expires_at = active_delegation.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= now_utc:
                raise ExpiredDelegationError(
                    f"Delegation '{active_delegation.id}' expired at {active_delegation.expires_at.isoformat()}"
                )

        return active_delegation
