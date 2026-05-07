"""Unit tests for Run.resume_from_retry domain method."""

from datetime import datetime, timezone

import pytest

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import RunStatusChanged
from src.contexts.symphony.domain.run.status import RunStatus


def _retry_pending_run() -> Run:
    run = Run.create(issue_id="ENG-1")
    run.set_status(RunStatus.GEN_SPEC)
    run.set_status(RunStatus.SPEC_PENDING)
    run.set_status(RunStatus.SPEC_APPROVED)
    run.set_status(RunStatus.GEN_PLAN)
    run.set_status(RunStatus.PLAN_PENDING)
    run.set_status(RunStatus.PLAN_APPROVED)
    run.mark_retry_pending(
        error="agent stalled", next_attempt_at=datetime.now(timezone.utc)
    )
    run.pull_events()
    return run


def test_resume_from_retry_transitions_to_plan_approved() -> None:
    run = _retry_pending_run()
    run.resume_from_retry()
    assert run.status == RunStatus.PLAN_APPROVED


def test_resume_from_retry_increments_attempt() -> None:
    run = _retry_pending_run()
    initial = run.attempt
    run.resume_from_retry()
    assert run.attempt == initial + 1


def test_resume_from_retry_clears_error_and_next_attempt() -> None:
    run = _retry_pending_run()
    assert run.error is not None
    assert run.next_attempt_at is not None
    run.resume_from_retry()
    assert run.error is None
    assert run.next_attempt_at is None


def test_resume_from_retry_emits_status_changed_event() -> None:
    run = _retry_pending_run()
    run.resume_from_retry()
    events = run.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], RunStatusChanged)
    assert events[0].from_status == RunStatus.RETRY_PENDING.value
    assert events[0].to_status == RunStatus.PLAN_APPROVED.value


def test_resume_from_retry_outside_retry_pending_raises() -> None:
    run = Run.create(issue_id="ENG-2")
    run.set_status(RunStatus.GEN_SPEC)
    run.pull_events()
    with pytest.raises(ValueError, match="RETRY_PENDING"):
        run.resume_from_retry()
