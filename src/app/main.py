import time
import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sentry_asgi import SentryMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.middleware.gzip import GZipMiddleware

from .database import Base
from .database.session import engine
from .api import api_router
from .rate_limiter import limiter

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
    description="Welcome to Secret Friend Generator's API documentation! Here you will be able to discover all of the ways you can interact with the API.",
    root_path="/api/v1",
)
api.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000 ; includeSubDomains"
    return response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path_template = request.url.path
        tags = {"method": request.method, "endpoint": path_template}

        try:
            start = time.perf_counter()
            response = await call_next(request)
            elapsed_time = time.perf_counter() - start
            tags.update({"status_code": response.status_code})
            log.debug(f"server.call.elapsed.{path_template}: {elapsed_time}")
        except Exception as e:
            log.error(f"server.call.exception.{path_template}: {e}")
            raise e
        return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StreamingResponse:
        try:
            return await call_next(request)
        except ValidationError as e:
            log.exception(e)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": e.errors()},
            )
        except ValueError as e:
            log.exception(e)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": [
                        {
                            "msg": "Invalid value.",
                            "loc": ["unknown"],
                            "type": "value_error",
                        }
                    ]
                },
            )
        except Exception as e:
            log.exception(e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": [
                        {
                            "msg": "Unexpected error.",
                            "loc": ["unknown"],
                            "type": "unknown_error",
                        }
                    ]
                },
            )


# Add Middleware
api.add_middleware(SentryMiddleware)
api.add_middleware(MetricsMiddleware)
api.add_middleware(ExceptionMiddleware)

api.include_router(api_router)

# Mount API to main app
app.mount("/api/v1", app=api)


# Utility Functions
def create_tables():
    """Creates database tables if they do not exist. Use only for development."""
    Base.metadata.create_all(bind=engine)


# Include API router
def include_routers(app: FastAPI):
    """Include all routers to the FastAPI application."""
    app.include_router(api_router)


# Application Startup
def start_application() -> FastAPI:
    """Initialize and configure the FastAPI application."""
    create_tables()
    include_routers(app)
    return app


# Main App
app = start_application()
