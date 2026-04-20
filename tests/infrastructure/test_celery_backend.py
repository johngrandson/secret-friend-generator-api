"""Tests for CeleryBackend — uses MagicMock, no real broker needed."""

from unittest.mock import MagicMock

from src.infrastructure.tasks.backend import CeleryBackend


def test_celery_backend_calls_send_task_with_name():
    """send() dispatches to the Celery app using the correct task name."""
    mock_app = MagicMock()
    backend = CeleryBackend(mock_app)

    backend.send("notifications.group_created", group_id=1, group_name="xmas")

    mock_app.send_task.assert_called_once_with(
        "notifications.group_created",
        kwargs={"group_id": 1, "group_name": "xmas"},
    )


def test_celery_backend_send_with_no_kwargs():
    """send() with no extra kwargs passes an empty dict to send_task."""
    mock_app = MagicMock()
    backend = CeleryBackend(mock_app)

    backend.send("some.task")

    mock_app.send_task.assert_called_once_with("some.task", kwargs={})


def test_celery_backend_send_passes_multiple_kwargs():
    """send() forwards all keyword arguments into the kwargs dict."""
    mock_app = MagicMock()
    backend = CeleryBackend(mock_app)

    backend.send("heavy.export", user_id=42, format="csv", locale="en")

    mock_app.send_task.assert_called_once_with(
        "heavy.export",
        kwargs={"user_id": 42, "format": "csv", "locale": "en"},
    )


def test_celery_backend_stores_app_reference():
    """CeleryBackend holds a reference to the Celery app passed at init."""
    mock_app = MagicMock()
    backend = CeleryBackend(mock_app)

    assert backend._app is mock_app


def test_celery_backend_send_called_exactly_once_per_invocation():
    """Each call to send() triggers exactly one send_task call."""
    mock_app = MagicMock()
    backend = CeleryBackend(mock_app)

    backend.send("task.a")
    backend.send("task.b")

    assert mock_app.send_task.call_count == 2
