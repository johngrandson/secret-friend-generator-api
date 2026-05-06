"""Unit tests for the ApprovalVerdict VO."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from src.contexts.symphony.domain.approval.verdict import ApprovalVerdict


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_accept_decision() -> None:
    verdict = ApprovalVerdict(
        decision="ACCEPT", approver_id="alice", timestamp=_now()
    )
    assert verdict.is_accepted() is True


def test_reject_decision() -> None:
    verdict = ApprovalVerdict(
        decision="REJECT",
        approver_id="bob",
        timestamp=_now(),
        comment="not ready",
    )
    assert verdict.is_accepted() is False
    assert verdict.comment == "not ready"


def test_is_frozen() -> None:
    verdict = ApprovalVerdict(
        decision="ACCEPT", approver_id="alice", timestamp=_now()
    )
    with pytest.raises(FrozenInstanceError):
        verdict.decision = "REJECT"  # type: ignore[misc]


def test_invalid_decision_raises() -> None:
    with pytest.raises(ValueError):
        ApprovalVerdict(
            decision="MAYBE",  # type: ignore[arg-type]
            approver_id="alice",
            timestamp=_now(),
        )


def test_blank_approver_id_raises() -> None:
    with pytest.raises(ValueError):
        ApprovalVerdict(decision="ACCEPT", approver_id="   ", timestamp=_now())
