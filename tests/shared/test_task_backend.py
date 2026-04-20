"""Tests for task backend dispatch in src/shared/task_backend.py."""

import logging
from unittest.mock import MagicMock

import pytest

import src.shared.task_backend as task_backend_module
from src.shared.task_backend import LoggingBackend, dispatch_task, set_backend


@pytest.fixture(autouse=True)
def restore_backend():
    """Restore original backend after each test to avoid global state pollution."""
    original = task_backend_module._backend
    yield
    task_backend_module._backend = original


def test_dispatch_task_delegates_to_backend() -> None:
    mock_backend = MagicMock()
    set_backend(mock_backend)

    dispatch_task("some.task", foo="bar", count=42)

    mock_backend.send.assert_called_once_with("some.task", foo="bar", count=42)


def test_set_backend_swaps_active_backend() -> None:
    first_backend = MagicMock()
    second_backend = MagicMock()

    set_backend(first_backend)
    dispatch_task("task.one")
    first_backend.send.assert_called_once_with("task.one")
    second_backend.send.assert_not_called()

    set_backend(second_backend)
    dispatch_task("task.two")
    second_backend.send.assert_called_once_with("task.two")
    # first backend receives no further calls after swap
    first_backend.send.assert_called_once()


def test_logging_backend_logs_task(caplog: pytest.LogCaptureFixture) -> None:
    backend = LoggingBackend()
    set_backend(backend)

    with caplog.at_level(logging.INFO, logger="src.shared.task_backend"):
        dispatch_task("notifications.welcome_email", user_id=7)

    assert any("notifications.welcome_email" in r.message for r in caplog.records)
