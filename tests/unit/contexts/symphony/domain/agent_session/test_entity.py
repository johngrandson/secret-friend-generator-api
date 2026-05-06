"""Unit tests for the AgentSession aggregate."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.agent_session.entity import AgentSession
from src.contexts.symphony.domain.agent_session.events import (
    AgentSessionCompleted,
    AgentSessionFailed,
    AgentSessionStarted,
)
from src.shared.agentic.agent_runner import TokenUsage


def test_create_emits_started_event() -> None:
    run_id = uuid4()
    session = AgentSession.create(run_id=run_id, model="claude-sonnet-4-6")
    events = session.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], AgentSessionStarted)
    assert events[0].run_id == run_id
    assert events[0].model == "claude-sonnet-4-6"
    assert session.is_active()


def test_create_rejects_blank_model() -> None:
    with pytest.raises(ValueError):
        AgentSession.create(run_id=uuid4(), model="   ")


def test_complete_records_usage_and_emits_event() -> None:
    session = AgentSession.create(run_id=uuid4(), model="claude")
    session.pull_events()
    usage = TokenUsage(input_tokens=100, output_tokens=50, total_tokens=150)
    session.complete(usage=usage)
    events = session.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], AgentSessionCompleted)
    assert events[0].usage == usage
    assert not session.is_active()


def test_complete_twice_raises() -> None:
    session = AgentSession.create(run_id=uuid4(), model="claude")
    session.complete()
    with pytest.raises(ValueError):
        session.complete()


def test_fail_emits_failed_event() -> None:
    session = AgentSession.create(run_id=uuid4(), model="claude")
    session.pull_events()
    session.fail("token budget exceeded")
    events = session.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], AgentSessionFailed)
    assert events[0].error == "token budget exceeded"
    assert not session.is_active()


def test_fail_blank_error_raises() -> None:
    session = AgentSession.create(run_id=uuid4(), model="claude")
    with pytest.raises(ValueError):
        session.fail("   ")


def test_record_usage_does_not_emit() -> None:
    session = AgentSession.create(run_id=uuid4(), model="claude")
    session.pull_events()
    session.record_usage(TokenUsage(total_tokens=42))
    assert session.pull_events() == []
    assert session.usage.total_tokens == 42
