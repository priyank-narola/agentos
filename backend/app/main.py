from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.registry import router as registry_router
from app.api.policy import router as policy_router
from app.api.gateway import router as gateway_router
from app.api.approval import router as approval_router

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)
app.include_router(registry_router)
app.include_router(policy_router)
app.include_router(gateway_router)
app.include_router(approval_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agentos-api"}


@app.get("/api/v1/version", tags=["system"])
def version() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version, "environment": settings.app_env}
