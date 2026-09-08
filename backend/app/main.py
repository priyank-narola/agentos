from typing import Any
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.config import settings
from app.api.registry import router as registry_router
from app.api.policy import router as policy_router
from app.api.gateway import router as gateway_router
from app.api.approval import router as approval_router
from app.api.demo import router as demo_router
from app.api.observability import router as observability_router
from app.api.demo_scenarios import router as demo_scenarios_router
from app.api.integration import router as integration_router
from app.api.webhook import router as webhook_router
from app.api.auth_tokens import router as auth_tokens_router
from app.api.deps import require_rest_auth
from app.api.mcp import mcp_app

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

# Control-plane routers require REST bearer authentication when it is enforced
# (any non-development deployment or REST_AUTH_REQUIRED=true). Public/system
# routes below are intentionally excluded.
app.include_router(registry_router, dependencies=[Depends(require_rest_auth)])
app.include_router(policy_router, dependencies=[Depends(require_rest_auth)])
app.include_router(gateway_router, dependencies=[Depends(require_rest_auth)])
app.include_router(approval_router, dependencies=[Depends(require_rest_auth)])
app.include_router(demo_router, dependencies=[Depends(require_rest_auth)])
app.include_router(observability_router, dependencies=[Depends(require_rest_auth)])
app.include_router(demo_scenarios_router, dependencies=[Depends(require_rest_auth)])
app.include_router(integration_router, dependencies=[Depends(require_rest_auth)])
app.include_router(webhook_router)
app.include_router(auth_tokens_router)





# Mount MCP Server
app.mount("/mcp", mcp_app)


@app.get("/.well-known/mcp", tags=["system"])
def well_known_mcp_metadata() -> dict[str, Any]:
    from app.api.mcp import get_mcp_protected_resource_metadata
    return get_mcp_protected_resource_metadata()


@app.get("/.well-known/oauth-protected-resource", tags=["system"])
def well_known_oauth_protected_resource() -> dict[str, Any]:
    """RFC 9728-style OAuth protected-resource metadata.

    Advertised to OAuth clients through the WWW-Authenticate
    ``resource_metadata`` parameter emitted by the MCP token validator.
    """
    from app.config import settings
    return {
        "resource": "urn:agentos:mcp:action-gateway",
        "authorization_servers": [settings.mcp_auth_issuer],
        "scopes_supported": ["agentos:execute", "mcp:execute_action"],
        "bearer_methods_supported": ["header"],
    }


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agentos-api"}



@app.get("/api/v1/version", tags=["system"])
def version() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version, "environment": settings.app_env}
