"""Unit tests for Plan.apply_verdict (ApprovalVerdict-based state transition)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.approval.verdict import ApprovalVerdict
from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.domain.plan.events import PlanApproved, PlanRejected


def _plan() -> Plan:
    p = Plan.create(run_id=uuid4(), version=1, content="plan content")
    p.pull_events()  # clear PlanCreated
    return p


def _accept() -> ApprovalVerdict:
    return ApprovalVerdict(
        decision="ACCEPT",
        approver_id="alice",
        timestamp=datetime.now(timezone.utc),
    )


def _reject(*, comment: str | None = "no") -> ApprovalVerdict:
    return ApprovalVerdict(
        decision="REJECT",
        approver_id="bob",
        timestamp=datetime.now(timezone.utc),
        comment=comment,
    )


def test_apply_verdict_accept_marks_approved_and_emits_event() -> None:
    plan = _plan()
    plan.apply_verdict(_accept())
    assert plan.approved_by == "alice"
    events = plan.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], PlanApproved)


def test_apply_verdict_reject_marks_rejected_and_emits_event() -> None:
    plan = _plan()
    plan.apply_verdict(_reject(comment="missing detail"))
    assert plan.rejection_reason == "missing detail"
    events = plan.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], PlanRejected)


def test_apply_verdict_reject_falls_back_when_comment_none() -> None:
    plan = _plan()
    plan.apply_verdict(_reject(comment=None))
    assert plan.rejection_reason == "rejected"


def test_apply_verdict_twice_raises() -> None:
    plan = _plan()
    plan.apply_verdict(_accept())
    with pytest.raises(ValueError):
        plan.apply_verdict(_reject())
