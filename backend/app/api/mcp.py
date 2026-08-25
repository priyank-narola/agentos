import hashlib
import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any, Optional

from mcp import MCPError
from mcp.server import MCPServer
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.auth import AuthError, TokenClaims, TokenValidator
from app.db.session import SessionLocal
from app.identity import AgentIdentityResolver, IdentityResolutionError, SecurityContext
from app.schemas import GatewayRequestCreate, GatewayResponse
from app.services.errors import RegistryConflictError
from app.services.gateway import GatewayIdempotencyConflict, GatewayService

logger = logging.getLogger(__name__)

# Request-scoped context variables for safe async & concurrent handling
request_authorization_var: ContextVar[Optional[str]] = ContextVar("request_authorization_var", default=None)
request_db_session_var: ContextVar[Optional[Session]] = ContextVar("request_db_session_var", default=None)


class MCPTransportContextMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that extracts the HTTP Authorization header from incoming
    MCP requests and populates the request-scoped context variable.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        auth_header = request.headers.get("authorization")
        token = request_authorization_var.set(auth_header)
        try:
            return await call_next(request)
        finally:
            request_authorization_var.reset(token)


mcp_server = MCPServer(
    name="AgentOS MCP Server",
    version="0.1.0",
    description="Secure Model Context Protocol Server for AgentOS Control Plane"
)

token_validator = TokenValidator()
identity_resolver = AgentIdentityResolver()

FORBIDDEN_PARAMETER_KEYS = {
    "principal_id",
    "agent_id",
    "delegation_id",
    "policy_id",
    "policy_effect",
    "policy_decision",
    "decision",
    "risk_level",
    "risk_score",
    "risk_classification",
    "approval_status",
    "approved",
    "override",
    "authorization",
    "authorization_override",
}


def sanitize_parameters(val: Any) -> Any:
    """
    Recursively remove security-sensitive authorization and identity override keys
    from parameter dictionaries or nested structures.
    """
    if isinstance(val, dict):
        return {
            k: sanitize_parameters(v)
            for k, v in val.items()
            if k not in FORBIDDEN_PARAMETER_KEYS
        }
    elif isinstance(val, list):
        return [sanitize_parameters(item) for item in val]
    return val


def generate_deterministic_idempotency_key(
    principal_id: uuid.UUID,
    agent_id: uuid.UUID,
    action_id: uuid.UUID,
    resource_id: uuid.UUID,
    parameters: dict[str, Any]
) -> str:
    """
    Generate a deterministic SHA-256 idempotency key using trusted identity context,
    target resource, action, and canonicalized business parameters.
    """
    canonical_params = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    raw_key = f"mcp:{principal_id}:{agent_id}:{action_id}:{resource_id}:{canonical_params}"
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return f"mcp-det-{digest[:32]}"


@mcp_server.tool(
    name="execute_action",
    description="Request execution of a formal action on a resource via the AgentOS Action Gateway (requires OAuth Bearer authentication via HTTP Authorization header)"
)
async def execute_action(
    action_id: str,
    resource_id: str,
    parameters: Optional[dict[str, Any]] = None,
    idempotency_key: Optional[str] = None
) -> str:
    """
    Request execution of a formal action on a resource via the AgentOS Action Gateway.

    SECURITY INVARIANTS:
    1. Authorization header is extracted EXCLUSIVELY from MCP transport request context.
    2. Identity (Principal + Agent + Delegation) is derived STRICTLY from verified token claims.
    3. Principal ID, Agent ID, Delegation ID, Policy overrides, Risk/Approval overrides, or
       Authorization tokens passed in tool arguments or parameters are STRIPPED / IGNORED.
    4. Action authorization is evaluated ONLY by the existing AgentOS Action Gateway.
    """
    # 1. Resolve Authorization Header from Transport Request Context EXCLUSIVELY
    raw_auth = request_authorization_var.get()

    if not raw_auth or not raw_auth.strip():
        logger.warning("MCP execute_action failed: Missing Authorization header in request context")
        raise MCPError(
            code=-32000,
            message="Authentication failed: Missing Authorization header in request context"
        )

    # 2. Authenticate Bearer Token
    try:
        claims = token_validator.validate_token(raw_auth.strip())
    except AuthError as e:
        logger.warning(f"MCP execute_action authentication error: {e.message}")
        raise MCPError(
            code=-32000,
            message=f"Authentication failed: {e.message}"
        ) from e

    # 3. Resolve DB Session from Request/Task ContextVar or open SessionLocal
    db = request_db_session_var.get()
    close_db = False
    if db is None:
        if SessionLocal is None:
            logger.error("MCP execute_action error: Database session unavailable")
            raise MCPError(code=-32000, message="Internal server error: Database session unavailable")
        db = SessionLocal()
        close_db = True

    try:
        # 4. Resolve Security Context (Principal + Agent + Delegation)
        try:
            security_ctx = identity_resolver.resolve_security_context(claims, db)
        except IdentityResolutionError as e:
            logger.warning(f"MCP execute_action identity resolution error: {e.message}")
            raise MCPError(
                code=-32000,
                message=f"Identity resolution failed: {e.message}"
            ) from e

        # 5. Validate UUID formats
        try:
            parsed_action_id = uuid.UUID(action_id.strip())
            parsed_resource_id = uuid.UUID(resource_id.strip())
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("MCP execute_action invalid UUID format provided")
            raise MCPError(
                code=-32602,  # Invalid params JSON-RPC code
                message="Invalid parameters: action_id and resource_id must be valid UUID strings"
            ) from e

        # 6. Sanitize parameters (Shallow & Nested Spoofing Defense)
        raw_params = parameters if parameters and isinstance(parameters, dict) else {}
        clean_params = sanitize_parameters(raw_params)

        # 7. Idempotency Key Resolution (Explicit or Deterministic Hash)
        if idempotency_key and idempotency_key.strip():
            key = idempotency_key.strip()
        else:
            key = generate_deterministic_idempotency_key(
                principal_id=security_ctx.principal.id,
                agent_id=security_ctx.agent.id,
                action_id=parsed_action_id,
                resource_id=parsed_resource_id,
                parameters=clean_params
            )

        # 8. Construct GatewayRequestCreate using TRUSTED principal_id & agent_id from security_ctx
        request_payload = GatewayRequestCreate(
            principal_id=security_ctx.principal.id,
            agent_id=security_ctx.agent.id,
            action_id=parsed_action_id,
            resource_id=parsed_resource_id,
            parameters=clean_params,
            idempotency_key=key
        )

        # 9. Submit to Existing Action Gateway
        gateway_service = GatewayService(db)
        try:
            response: GatewayResponse = gateway_service.submit(request_payload)
            return response.model_dump_json()
        except GatewayIdempotencyConflict as e:
            logger.warning(f"MCP Gateway idempotency conflict: {str(e)}")
            raise MCPError(
                code=-32000,
                message="Gateway conflict: Idempotency key was already used with different request parameters"
            ) from e
        except RegistryConflictError as e:
            logger.warning(f"MCP Gateway registry conflict: {str(e)}")
            raise MCPError(
                code=-32000,
                message="Gateway conflict: Referenced resource or capability relationship is invalid"
            ) from e
        except MCPError:
            raise
        except Exception as e:
            db.rollback()
            logger.exception("Unexpected error during MCP execute_action gateway submission")
            raise MCPError(
                code=-32000,
                message="Internal server error during action execution"
            ) from e

    finally:
        if close_db and db:
            db.close()


mcp_app = mcp_server.sse_app(host="0.0.0.0")
mcp_app.add_middleware(MCPTransportContextMiddleware)
