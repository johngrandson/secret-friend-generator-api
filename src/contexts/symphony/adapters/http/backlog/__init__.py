"""Backlog HTTP adapter package."""

from src.contexts.symphony.adapters.http.backlog.router import router
import src.contexts.symphony.adapters.http.backlog.routes  # noqa: F401 — triggers route registration

__all__ = ["router"]
