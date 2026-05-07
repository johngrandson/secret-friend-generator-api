"""Unit tests for Spec.apply_verdict (ApprovalVerdict-based state transition)."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.approval.verdict import ApprovalVerdict
from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.domain.spec.events import SpecApproved, SpecRejected


def _spec() -> Spec:
    s = Spec.create(run_id=uuid4(), version=1, content="content")
    s.pull_events()  # clear SpecCreated
    return s


def _accept(*, comment: str | None = None) -> ApprovalVerdict:
    return ApprovalVerdict(
        decision="ACCEPT",
        approver_id="alice",
        timestamp=datetime.now(timezone.utc),
        comment=comment,
    )


def _reject(*, comment: str | None = "needs work") -> ApprovalVerdict:
    return ApprovalVerdict(
        decision="REJECT",
        approver_id="bob",
        timestamp=datetime.now(timezone.utc),
        comment=comment,
    )


def test_apply_verdict_accept_marks_approved() -> None:
    spec = _spec()
    spec.apply_verdict(_accept())
    assert spec.approved_by == "alice"
    assert spec.approved_at is not None
    assert spec.is_pending() is False


def test_apply_verdict_accept_emits_spec_approved_event() -> None:
    spec = _spec()
    spec.apply_verdict(_accept())
    events = spec.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], SpecApproved)


def test_apply_verdict_reject_marks_rejected_and_uses_comment() -> None:
    spec = _spec()
    spec.apply_verdict(_reject(comment="missing approach"))
    assert spec.rejection_reason == "missing approach"
    assert spec.is_pending() is False


def test_apply_verdict_reject_falls_back_when_comment_missing() -> None:
    spec = _spec()
    spec.apply_verdict(_reject(comment=None))
    assert spec.rejection_reason == "rejected"


def test_apply_verdict_reject_emits_spec_rejected_event() -> None:
    spec = _spec()
    spec.apply_verdict(_reject())
    events = spec.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], SpecRejected)


def test_apply_verdict_twice_raises_write_once() -> None:
    spec = _spec()
    spec.apply_verdict(_accept())
    with pytest.raises(ValueError):
        spec.apply_verdict(_accept())
