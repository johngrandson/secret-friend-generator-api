"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.adapters.http.user import router as user_router
from src.infrastructure.containers import Container
from src.infrastructure.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db(app.container.core.db_engine())  # type: ignore[attr-defined]
    yield


def create_app() -> FastAPI:
    container = Container()
    container.wire()

    app = FastAPI(
        title="Python AI Starter — Clean Architecture",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.container = container  # type: ignore[attr-defined]
    app.include_router(user_router)
    return app


app = create_app()
