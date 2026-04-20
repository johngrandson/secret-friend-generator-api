"""Tests for Celery app config helpers: _queue_arguments, _build_queues, _parse_task_routes.

All tests are pure function tests — no fixtures or broker needed.
"""

import pytest

from src.infrastructure.messaging.celery.app import (
    _build_queues,
    _parse_task_routes,
    _queue_arguments,
)


# ---------------------------------------------------------------------------
# _queue_arguments
# ---------------------------------------------------------------------------


def test_queue_arguments_classic_returns_empty_dict():
    """'classic' queue type requires no x-arguments."""
    result = _queue_arguments("classic")
    assert result == {}


def test_queue_arguments_quorum_returns_x_queue_type():
    """'quorum' queue type must declare x-queue-type: quorum."""
    result = _queue_arguments("quorum")
    assert result == {"x-queue-type": "quorum"}


def test_queue_arguments_invalid_raises_value_error():
    """An unknown queue type raises ValueError with a descriptive message."""
    with pytest.raises(ValueError, match="Invalid CELERY_QUEUE_TYPE"):
        _queue_arguments("sharded")


# ---------------------------------------------------------------------------
# _build_queues
# ---------------------------------------------------------------------------


def test_build_queues_default_only_when_no_extras():
    """When extra_names is empty, only the 'default' queue is declared."""
    queues = _build_queues("classic", "")
    names = [q.name for q in queues]
    assert names == ["default"]


def test_build_queues_includes_extras():
    """Extra queue names are appended after 'default'."""
    queues = _build_queues("classic", "notifications,heavy")
    names = [q.name for q in queues]
    assert names == ["default", "notifications", "heavy"]


def test_build_queues_deduplicates_default():
    """Listing 'default' in extra_names does not produce a duplicate queue."""
    queues = _build_queues("classic", "default,notifications")
    names = [q.name for q in queues]
    assert names.count("default") == 1
    assert "notifications" in names


def test_build_queues_strips_whitespace():
    """Whitespace around extra queue names is stripped before declaring."""
    queues = _build_queues("classic", " notifications , heavy ")
    names = [q.name for q in queues]
    assert "notifications" in names
    assert "heavy" in names


def test_build_queues_quorum_sets_queue_arguments():
    """Queues built with 'quorum' type carry the x-queue-type argument."""
    queues = _build_queues("quorum", "")
    assert queues[0].queue_arguments == {"x-queue-type": "quorum"}


def test_build_queues_classic_has_no_queue_arguments():
    """Queues built with 'classic' type carry no extra x-arguments."""
    queues = _build_queues("classic", "")
    assert queues[0].queue_arguments == {}


# ---------------------------------------------------------------------------
# _parse_task_routes
# ---------------------------------------------------------------------------


def test_parse_task_routes_empty_string_returns_empty():
    """An empty string produces an empty routes dict."""
    result = _parse_task_routes("")
    assert result == {}


def test_parse_task_routes_empty_json_returns_empty():
    """A JSON '{}' string produces an empty routes dict."""
    result = _parse_task_routes("{}")
    assert result == {}


def test_parse_task_routes_valid_json_returns_celery_format():
    """A valid JSON mapping is transformed into Celery's task_routes format."""
    raw = '{"notifications.*": "notifications", "heavy.*": "heavy"}'
    result = _parse_task_routes(raw)
    assert result == {
        "notifications.*": {"queue": "notifications"},
        "heavy.*": {"queue": "heavy"},
    }


def test_parse_task_routes_single_entry():
    """A single-entry JSON object is parsed correctly."""
    result = _parse_task_routes('{"email.send": "email"}')
    assert result == {"email.send": {"queue": "email"}}


def test_parse_task_routes_invalid_json_raises():
    """Malformed JSON raises ValueError."""
    with pytest.raises(ValueError, match="valid JSON object"):
        _parse_task_routes("{not valid json}")


def test_parse_task_routes_non_dict_raises():
    """A JSON array instead of object raises ValueError."""
    with pytest.raises(ValueError, match="JSON object"):
        _parse_task_routes('["notifications", "heavy"]')
