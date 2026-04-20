"""Celery implementation of the TaskBackend protocol.

Uses send_task() for dynamic dispatch — the FastAPI process never
imports @shared_task definitions. Only the Celery worker does.
"""
import logging

from celery import Celery

log = logging.getLogger(__name__)


class CeleryBackend:
    """Production backend — dispatches tasks to RabbitMQ via Celery."""

    def __init__(self, app: Celery) -> None:
        self._app = app

    def send(self, task_name: str, **kwargs: object) -> None:
        log.debug("task dispatched via celery: %s — %s", task_name, kwargs)
        self._app.send_task(task_name, kwargs=kwargs)
