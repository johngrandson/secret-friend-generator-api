import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sentry_asgi import SentryMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.api.middleware import ExceptionMiddleware, MetricsMiddleware
from src.api.router import api_router
from src.api.agents.dependencies import init_agents_registry, shutdown_agents
from src.domain.lifecycle import register_all_handlers
from src.infrastructure.persistence import Base, engine
from src.shared.config import settings
from src.shared.rate_limiter import limiter

log = logging.getLogger(__name__)


def _create_tables() -> None:
    """Creates database tables if they do not exist. Use only for development."""
    Base.metadata.create_all(bind=engine)


def _not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": [{"msg": "Not Found."}]},
    )


@asynccontextmanager
async def _api_lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown lifecycle for the API sub-application."""
    await init_agents_registry()
    yield
    await shutdown_agents()


# ── Main app (outer shell) ───────────────────────────────────────────────────

app = FastAPI(exception_handlers={404: _not_found_handler}, openapi_url="")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000 ; includeSubDomains"
    return response


# ── API sub-application ──────────────────────────────────────────────────────

api = FastAPI(
    title="Secret Friend Generator",
    description="Welcome to Secret Friend Generator's API documentation!",
    root_path="/api/v1",
    lifespan=_api_lifespan,
)
api.add_middleware(GZipMiddleware, minimum_size=1000)
api.add_middleware(SentryMiddleware)
api.add_middleware(MetricsMiddleware)
api.add_middleware(ExceptionMiddleware)
api.include_router(api_router)

app.mount("/api/v1", app=api)

# ── Bootstrap (run at import time) ───────────────────────────────────────────

_create_tables()
register_all_handlers()

if settings.ENV != "test":
    from src.infrastructure.tasks import CeleryBackend, celery_app
    from src.shared.task_backend import set_backend

    set_backend(CeleryBackend(celery_app))
