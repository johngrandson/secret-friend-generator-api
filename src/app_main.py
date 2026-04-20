import logging
from collections.abc import Awaitable, Callable

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
from src.domain.shared.database_base import Base
from src.domain.shared.database_session import engine
from src.shared.rate_limiter_config import limiter

log = logging.getLogger(__name__)

# Application Setup
exception_handlers = {
    404: lambda request, exc: JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": [{"msg": "Not Found."}]},
    )
}

# Initialize main app
app = FastAPI(exception_handlers=exception_handlers, openapi_url="")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Initialize API app
api = FastAPI(
    title="Secret Friend Generator",
    description="Welcome to Secret Friend Generator's API documentation!",
    root_path="/api/v1",
)
api.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware
@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000 ; includeSubDomains"
    return response


# Add Middleware to API
api.add_middleware(SentryMiddleware)
api.add_middleware(MetricsMiddleware)
api.add_middleware(ExceptionMiddleware)

api.include_router(api_router)

# Mount API to main app
app.mount("/api/v1", app=api)


@api.on_event("startup")
async def startup_agents():
    await init_agents_registry()


@api.on_event("shutdown")
async def shutdown_agents_cleanup():
    await shutdown_agents()


def create_tables():
    """Creates database tables if they do not exist. Use only for development."""
    Base.metadata.create_all(bind=engine)


def start_application() -> FastAPI:
    create_tables()
    register_all_handlers()
    return app


app = start_application()
