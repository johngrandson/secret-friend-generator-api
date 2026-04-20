"""Task queue infrastructure — Celery app, backend, and task definitions.

Import from here for convenience:
    from src.infrastructure.tasks import celery_app, CeleryBackend
"""
from src.infrastructure.tasks.app import celery_app
from src.infrastructure.tasks.backend import CeleryBackend

__all__ = ["CeleryBackend", "celery_app"]
