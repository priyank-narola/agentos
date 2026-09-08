import hashlib
import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any, Optional

from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from mcp import MCPError
from mcp.server import MCPServer

from app.auth import AuthError, TokenClaims, TokenValidator
from app.db.session import SessionLocal
from app.identity import AgentIdentityResolver, IdentityResolutionError, SecurityContext
from app.schemas import GatewayRequestCreate, GatewayResponse
from app.services.errors import RegistryConflictError
from app.services.gateway import GatewayIdempotencyConflict, GatewayService
from app.api.ratelimit import check_rate_limit

logger = logging.getLogger(__name__)

SUPPORTED_MCP_VERSIONS = {"2024-11-05", "2024-11-25", "latest"}

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
    raw_auth = request_authorization_var.get()
    db = request_db_session_var.get()
    try:
        result_dict = execute_action_core(
            action_id=action_id,
            resource_id=resource_id,
            raw_auth=raw_auth,
            parameters=parameters,
            idempotency_key=idempotency_key,
            db=db
        )
        return json.dumps(result_dict, default=str)
    except AuthError as e:
        raise MCPError(code=-32000, message=f"Authentication failed: {e.message}") from e
    except IdentityResolutionError as e:
        raise MCPError(code=-32000, message=f"Identity resolution failed: {e.message}") from e
    except MCPError:
        raise
    except Exception as e:
        logger.exception("Unexpected error during MCP execute_action tool call")
        raise MCPError(code=-32000, message="Internal server error during action execution") from e




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


def execute_action_core(
    action_id: str,
    resource_id: str,
    raw_auth: Optional[str],
    parameters: Optional[dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
    db: Optional[Session] = None
) -> dict[str, Any]:
    """Core execution logic for execute_action tool shared across transport endpoints."""
    if not raw_auth or not raw_auth.strip():
        raise MCPError(
            code=-32000,
            message="Authentication failed: Missing Authorization header in request context"
        )

    claims = token_validator.validate_token(raw_auth.strip())

    close_db = False
    if db is None:
        db = request_db_session_var.get()

    if db is None:
        from app.main import app
        from app.db.session import get_db
        if get_db in app.dependency_overrides:
            db_gen = app.dependency_overrides[get_db]()
            db = next(db_gen)
            close_db = True
        elif SessionLocal is not None:
            db = SessionLocal()
            close_db = True
        else:
            raise MCPError(code=-32000, message="Internal server error: Database session unavailable")


    try:
        security_ctx = identity_resolver.resolve_security_context(claims, db)

        try:
            parsed_action_id = uuid.UUID(action_id.strip())
            parsed_resource_id = uuid.UUID(resource_id.strip())
        except (ValueError, TypeError, AttributeError) as e:
            raise MCPError(
                code=-32602,
                message="Invalid parameters: action_id and resource_id must be valid UUID strings"
            ) from e

        raw_params = parameters if parameters and isinstance(parameters, dict) else {}
        clean_params = sanitize_parameters(raw_params)

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

        request_payload = GatewayRequestCreate(
            principal_id=security_ctx.principal.id,
            agent_id=security_ctx.agent.id,
            action_id=parsed_action_id,
            resource_id=parsed_resource_id,
            parameters=clean_params,
            idempotency_key=key
        )

        gateway_service = GatewayService(db)
        try:
            response: GatewayResponse = gateway_service.submit(request_payload)
            return response.model_dump()
        except GatewayIdempotencyConflict as e:
            raise MCPError(
                code=-32000,
                message="Gateway conflict: Idempotency key was already used with different request parameters"
            ) from e
        except RegistryConflictError as e:
            raise MCPError(
                code=-32000,
                message="Gateway conflict: Referenced resource or capability relationship is invalid"
            ) from e
    finally:
        if close_db and db:
            db.close()


mcp_app = FastAPI(title="AgentOS MCP Streamable HTTP Gateway", version="1.0.0")
mcp_app.add_middleware(MCPTransportContextMiddleware)


@mcp_app.get("/metadata", response_model=dict[str, Any])
@mcp_app.get("/.well-known/mcp", response_model=dict[str, Any])
@mcp_app.get("/", response_model=dict[str, Any])
def get_mcp_protected_resource_metadata() -> dict[str, Any]:
    """Exposes protected resource discovery metadata for remote MCP clients according to standard MCP spec."""
    return {
        "name": "AgentOS MCP Server",
        "version": "0.1.0",
        "protocol_version": "2024-11-05",
        "transport": "Streamable-HTTP",
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False}
        },
        "protected_resource": {
            "resource_id": "urn:agentos:mcp:action-gateway",
            "authorization_type": "Bearer",
            "scopes": ["mcp:execute_action"]
        }
    }


@mcp_app.post("/", response_model=dict[str, Any])
@mcp_app.post("/messages", response_model=dict[str, Any])
@mcp_app.post("/v1/messages", response_model=dict[str, Any])
async def handle_mcp_streamable_http_message(request: Request, _rate_limit: None = Depends(check_rate_limit)) -> Response:

    """
    Main MCP Streamable HTTP JSON-RPC Message Endpoint.
    Handles initialize, tools/list, tools/call, ping, and notifications over HTTP POST.
    """
    # 1. Check Protocol Version Header if provided
    proto_version = request.headers.get("mcp-protocol-version", "2024-11-05")
    if proto_version not in SUPPORTED_MCP_VERSIONS:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": f"Unsupported MCP-Protocol-Version '{proto_version}'"}
            }
        )

    # 2. Check Content-Type
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type and "application/json-rpc" not in content_type and content_type != "":
        return JSONResponse(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Content-Type. Expected application/json"}
            }
        )

    # 3. Check Authentication Header (Fail Closed)
    raw_auth = request.headers.get("authorization")
    if not raw_auth or not raw_auth.strip():
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": 'Bearer realm="AgentOS", error="invalid_token", scope="mcp:execute_action"'},
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": "Authentication failed: Missing Authorization header in request context"}
            }
        )

    # Validate Bearer Token format
    try:
        token_validator.validate_token(raw_auth.strip())
    except AuthError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": f'Bearer realm="AgentOS", error="invalid_token", error_description="{e.message}"'},
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32000, "message": f"Authentication failed: {e.message}"}
            }
        )

    # Parse JSON-RPC Payload
    try:
        body_bytes = await request.body()
        if not body_bytes:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error: Empty request body"}}
            )
        data = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {str(e)}"}}
        )

    req_id = data.get("id")
    method = data.get("method")
    params = data.get("params", {})

    if not method:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"jsonrpc": "2.0", "id": req_id, "error": {"code": -32600, "message": "Invalid Request: missing method"}}
        )

    # Dispatch JSON-RPC methods
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False}
                },
                "serverInfo": {
                    "name": "AgentOS MCP Server",
                    "version": "0.1.0"
                }
            }
        })

    elif method == "notifications/initialized":
        return Response(status_code=status.HTTP_202_ACCEPTED)

    elif method == "ping":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        })

    elif method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "execute_action",
                        "description": "Request execution of a formal action on a resource via the AgentOS Action Gateway",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "action_id": {"type": "string", "description": "Action UUID"},
                                "resource_id": {"type": "string", "description": "Resource UUID"},
                                "parameters": {"type": "object", "description": "Action business parameters"},
                                "idempotency_key": {"type": "string", "description": "Optional idempotency key"}
                            },
                            "required": ["action_id", "resource_id"]
                        }
                    }
                ]
            }
        })

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name != "execute_action":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"}
            })

        action_id = args.get("action_id")
        resource_id = args.get("resource_id")
        parameters = args.get("parameters")
        idempotency_key = args.get("idempotency_key")

        if not action_id or not resource_id:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": "Invalid parameters: action_id and resource_id are required"}
            })

        try:
            result_dict = execute_action_core(
                action_id=str(action_id),
                resource_id=str(resource_id),
                raw_auth=raw_auth,
                parameters=parameters,
                idempotency_key=idempotency_key
            )
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_dict, default=str)
                        }
                    ]
                }
            })

        except MCPError as e:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": e.code, "message": e.message}
            })
        except AuthError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": f'Bearer realm="AgentOS", error="invalid_token", error_description="{e.message}"'},
                content={"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": f"Authentication failed: {e.message}"}}
            )
        except IdentityResolutionError as e:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": f"Identity resolution failed: {e.message}"}
            })
        except Exception as e:
            logger.exception("Error executing tool call in MCP Streamable HTTP")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": f"Internal server error: {str(e)}"}
            })

    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"}
        })


# Backward Compatibility: Legacy SSE Endpoint
@mcp_app.get("/sse")
@mcp_app.post("/sse")
def legacy_sse_endpoint() -> Response:
    """Legacy MCP SSE Endpoint (Deprecated). Active until 2026-12-31."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        headers={"Deprecation": "@1735689600", "Sunset": "Thu, 31 Dec 2026 23:59:59 GMT"},
        content={
            "status": "deprecated",
            "message": "SSE transport is deprecated. Use MCP Streamable HTTP POST at /mcp",
            "migration_target": "/mcp"
        }
    )
