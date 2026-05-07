"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from src.contexts.identity.adapters.http.user import router as user_router
from src.contexts.symphony.adapters.http.backlog import router as backlog_router
from src.contexts.symphony.adapters.http.run import router as run_router
from src.contexts.symphony.adapters.http.spec import router as spec_router
from src.contexts.symphony.adapters.http.plan import router as plan_router
from src.contexts.tenancy.adapters.http.organization import (
    router as organization_router,
)
from src.infrastructure.containers import Container, get_container_from_app
from src.infrastructure.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    container = get_container_from_app(app)
    engine: AsyncEngine = container.core.db_engine()
    await init_db(engine)
    yield


def create_app() -> FastAPI:
    container = Container()
    container.wire()

    app = FastAPI(
        title="Python AI Starter — Clean Architecture",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.container = container
    app.include_router(user_router)
    app.include_router(run_router)
    app.include_router(spec_router)
    app.include_router(plan_router)
    app.include_router(backlog_router)
    app.include_router(organization_router)
    return app


app = create_app()
