import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure monorepo package directories are on sys.path
_current = Path(__file__).resolve().parent
for _candidate in (_current.parent, _current.parent.parent, _current.parent.parent.parent):
    _packages = _candidate / "packages"
    if _packages.is_dir():
        for _pkg in _packages.iterdir():
            if _pkg.is_dir() and str(_pkg) not in sys.path:
                sys.path.insert(0, str(_pkg))
        _services = _candidate / "services"
        if _services.is_dir():
            for _srv in _services.iterdir():
                if _srv.is_dir() and str(_srv) not in sys.path:
                    sys.path.insert(0, str(_srv))
        _connectors = _candidate / "connectors"
        if _connectors.is_dir() and str(_connectors) not in sys.path:
            sys.path.insert(0, str(_connectors))
        break

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine, Base
import app.models.tenant
import app.models.workflow
import app.models.run
import app.models.dlq
import app.models.incident
import app.models.agent
import app.models.schema_snapshot
from app.routers import (
    health,
    overview,
    connections,
    workflows,
    runs,
    agents,
    incidents,
    events,
    audit,
    tenants,
    users,
    api_keys,
    webhooks,
    observability,
    assistant,
    scripting,
    demo,
    search,
)
from app.middleware.telemetry_middleware import TelemetryMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.input_validator import InputValidatorMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

import logging
logger = logging.getLogger("flowmesh.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for connection pools and graceful shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.environment in ("development", "test"):
        from app.database import AsyncSessionLocal
        from app.models.tenant import Tenant
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            stmt = select(Tenant).where(Tenant.id == "tenant_acme")
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                session.add(Tenant(id="tenant_acme", name="Acme Global Corp (Demo)", slug="acme-corp", is_active=True))
                session.add(Tenant(id="tenant_prod", name="Production Workspace (Clean)", slug="production-workspace", is_active=True))
                session.add(Tenant(id="tenant_beta", name="Beta Logistics Inc", slug="beta-logistics", is_active=True))
                await session.commit()

    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="FlowMesh API Gateway",
        description="Client-owned, cloud-neutral enterprise integration and workflow platform.",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(SecurityHeadersMiddleware)

    app.add_middleware(RateLimitMiddleware)

    app.add_middleware(InputValidatorMiddleware)

    app.add_middleware(TelemetryMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )

    app.include_router(health.router)
    app.include_router(observability.router)
    app.include_router(overview.router)
    app.include_router(tenants.router)
    app.include_router(users.router)
    app.include_router(api_keys.router)
    app.include_router(connections.router)
    app.include_router(workflows.router)
    app.include_router(runs.router)
    app.include_router(agents.router)
    app.include_router(incidents.router)
    app.include_router(events.router)
    app.include_router(audit.router)
    app.include_router(webhooks.router)
    app.include_router(assistant.router)
    app.include_router(scripting.router)
    app.include_router(demo.router)
    app.include_router(search.router)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An internal server error occurred. Check server logs for details.",
                "path": request.url.path,
                "request_id": request.headers.get("x-request-id", "unknown"),
            },
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
