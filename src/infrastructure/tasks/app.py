"""Celery application factory.

Creates and configures the Celery instance with RabbitMQ as broker.
Worker entrypoint: celery -A src.infrastructure.tasks.app worker --loglevel=info
"""
from celery import Celery

from src.shared.config import settings


def make_celery() -> Celery:
    """Create a configured Celery app from application settings."""
    app = Celery("secret_santa")
    app.conf.update(
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )
    app.autodiscover_tasks(["src.infrastructure.tasks"])
    return app


celery_app = make_celery()
