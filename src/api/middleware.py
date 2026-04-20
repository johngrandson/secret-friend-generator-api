"""API middleware — metrics and exception handling.

ExceptionMiddleware acts as Phoenix's FallbackController: it maps
domain exceptions to HTTP status codes so routes stay clean.
"""
import logging
import time

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.domain.shared.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)

log = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path_template = request.url.path
        try:
            start = time.perf_counter()
            response = await call_next(request)
            elapsed_time = time.perf_counter() - start
            log.debug(f"server.call.elapsed.{path_template}: {elapsed_time}")
        except Exception as e:
            log.error(f"server.call.exception.{path_template}: {e}")
            raise e
        return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Maps domain exceptions to HTTP responses (FallbackController pattern)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except NotFoundError as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": [{"msg": str(e)}]},
            )
        except ConflictError as e:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={"detail": [{"msg": str(e)}]},
            )
        except BusinessRuleError as e:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": [{"msg": str(e)}]},
            )
        except ValidationError as e:
            log.exception(e)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": e.errors()},
            )
        except Exception as e:
            log.exception(e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": [{"msg": "Unexpected error."}]},
            )
