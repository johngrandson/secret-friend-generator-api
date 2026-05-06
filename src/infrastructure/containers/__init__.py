"""Public entry point for the DI container — re-exports the root Container."""

from fastapi import FastAPI, Request

from src.infrastructure.containers.root import Container


def get_container(request: Request) -> Container:
    """Return the typed root Container from a FastAPI Request.

    Replaces direct access to ``request.app.state.container`` (which is ``Any``
    via Starlette's :class:`~starlette.datastructures.State`) with a properly
    typed accessor. Use in route deps and any code that already has a Request.
    """
    container: Container = request.app.state.container
    return container


def get_container_from_app(app: FastAPI) -> Container:
    """Return the typed root Container directly from a FastAPI app.

    Use in lifespan, factory code, and tests where the app handle is in scope
    but no Request exists yet.
    """
    container: Container = app.state.container
    return container


__all__ = ["Container", "get_container", "get_container_from_app"]
