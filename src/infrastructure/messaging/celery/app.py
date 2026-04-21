"""Celery application factory.

Creates and configures the Celery instance from application settings.
Supports configurable RabbitMQ queue types (classic/quorum), task routing,
and extra queue declarations — all driven by environment variables.

Worker entrypoint:
    celery -A src.infrastructure.messaging.celery.app worker \\
        --loglevel=info --pool=prefork

Pool options (pass as --pool flag, not an app setting):
    prefork  — CPU-bound tasks (Celery default, uses multiprocessing)
    threads  — I/O-bound tasks (email, HTTP calls)
    gevent   — high-concurrency I/O (requires: pip install gevent)
    solo     — single-threaded, useful for debugging
"""

import json
import logging

from celery import Celery
from kombu import Exchange, Queue

from src.shared.config import RABBITMQ_QUEUE_TYPES, settings

log = logging.getLogger(__name__)

# The queue every unrouted task lands on.
_DEFAULT_QUEUE = "default"


def _queue_arguments(queue_type: str) -> dict[str, str]:
    """Return RabbitMQ x-arguments for the requested queue type.

    Args:
        queue_type: "classic" or "quorum".

    Returns:
        Dict of AMQP x-arguments to pass when declaring the queue.
    """
    if queue_type not in RABBITMQ_QUEUE_TYPES:
        raise ValueError(
            f"Invalid CELERY_QUEUE_TYPE '{queue_type}'. "
            f"Must be one of: {RABBITMQ_QUEUE_TYPES}"
        )
    if queue_type == "quorum":
        return {"x-queue-type": "quorum"}
    return {}


def _build_queues(queue_type: str, extra_names: str) -> list[Queue]:
    """Declare the default queue plus any extras, all with the same queue type.

    Args:
        queue_type: RabbitMQ queue type ("classic" or "quorum").
        extra_names: Comma-separated string of additional queue names.

    Returns:
        List of kombu Queue objects ready to pass to task_queues.
    """
    args = _queue_arguments(queue_type)

    names: list[str] = [_DEFAULT_QUEUE]
    for name in extra_names.split(","):
        name = name.strip()
        if name and name not in names:
            names.append(name)

    queues = []
    for name in names:
        exchange = Exchange(name, type="direct")
        queues.append(Queue(name, exchange, routing_key=name, queue_arguments=args))

    log.debug("celery queues declared: %s (type=%s)", names, queue_type)
    return queues


def _parse_task_routes(raw: str) -> dict[str, dict[str, str]]:
    """Parse CELERY_TASK_ROUTES JSON string into Celery's task_routes format.

    Input JSON:  {"notifications.*": "notifications", "heavy.*": "heavy"}
    Output dict: {"notifications.*": {"queue": "notifications"}, ...}

    Args:
        raw: JSON object string mapping task pattern → queue name.

    Returns:
        Dict in the format Celery expects for task_routes.

    Raises:
        ValueError: If the JSON is invalid or not a flat object.
    """
    if not raw or raw.strip() == "{}":
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"CELERY_TASK_ROUTES must be a valid JSON object. Got: {raw!r}"
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError(
            f"CELERY_TASK_ROUTES must be a JSON object ({{...}}). Got: {type(parsed)}"
        )
    return {pattern: {"queue": queue} for pattern, queue in parsed.items()}


def make_celery() -> Celery:
    """Create a configured Celery app from application settings.

    Configuration is driven entirely by environment variables / .env file.
    See src/shared/config.py for all CELERY_* settings.

    Returns:
        A fully configured Celery instance.
    """
    app = Celery("app")

    task_queues = _build_queues(
        settings.CELERY_QUEUE_TYPE, settings.CELERY_EXTRA_QUEUES
    )
    task_routes = _parse_task_routes(settings.CELERY_TASK_ROUTES)

    app.conf.update(
        # Broker / backend
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND,
        # Serialization
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        # Time
        timezone="UTC",
        enable_utc=True,
        # Reliability
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        # Test / eager mode — tasks run synchronously when True
        task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
        # Queue declarations
        task_queues=task_queues,
        task_default_queue=_DEFAULT_QUEUE,
        task_default_exchange=_DEFAULT_QUEUE,
        task_default_routing_key=_DEFAULT_QUEUE,
        # Task routing (empty dict = everything goes to default queue)
        task_routes=task_routes,
    )

    app.autodiscover_tasks(["src.infrastructure.messaging.celery.workers"])
    return app


celery_app = make_celery()
