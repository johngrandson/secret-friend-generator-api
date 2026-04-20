"""Task backend abstraction — deferred async work.

Defines a simple interface for dispatching background tasks.
The default backend logs the task (no-op). When Celery or another
task queue is added, swap the backend implementation — callers
don't change.

Usage:
    from src.shared.task_backend import dispatch_task
    dispatch_task("notifications.send_welcome_email", group_id=group.id)

To swap backend (when Celery is ready):
    from src.shared.task_backend import set_backend
    set_backend(CeleryBackend(celery_app))
"""

import logging
from typing import Protocol

log = logging.getLogger(__name__)


class TaskBackend(Protocol):
    """Interface for task dispatch backends."""

    def send(self, task_name: str, **kwargs: object) -> None:
        """Dispatch a named task with keyword arguments."""
        ...


class LoggingBackend:
    """Default backend — logs the task without executing it.

    Useful for development and testing. Replace with CeleryBackend
    or any other implementation in production.
    """

    def send(self, task_name: str, **kwargs: object) -> None:
        log.info("task dispatched (no-op): %s — %s", task_name, kwargs)


# ── Global backend registry ─────────────────────────────────────────────────

_backend: TaskBackend = LoggingBackend()


def set_backend(backend: TaskBackend) -> None:
    """Swap the task backend. Call at app startup."""
    global _backend
    _backend = backend


def dispatch_task(task_name: str, **kwargs: object) -> None:
    """Dispatch a background task via the configured backend."""
    _backend.send(task_name, **kwargs)
