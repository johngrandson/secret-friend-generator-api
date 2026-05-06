"""Unit tests for the PullRequest aggregate."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.pull_request.entity import PullRequest
from src.contexts.symphony.domain.pull_request.events import PROpened, PRUpdated


def _open_pr(**overrides: object) -> PullRequest:
    defaults: dict[str, object] = dict(
        run_id=uuid4(),
        number=42,
        url="https://github.com/x/y/pull/42",
        branch="feat/x",
        base_branch="main",
    )
    defaults.update(overrides)
    return PullRequest.open(**defaults)  # type: ignore[arg-type]


def test_open_emits_propened_event() -> None:
    pr = _open_pr()
    events = pr.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], PROpened)
    assert events[0].number == 42
    assert pr.is_draft is True


def test_open_rejects_invalid_number() -> None:
    with pytest.raises(ValueError):
        _open_pr(number=0)


@pytest.mark.parametrize("field", ["url", "branch", "base_branch"])
def test_open_rejects_blank_strings(field: str) -> None:
    with pytest.raises(ValueError):
        _open_pr(**{field: "   "})


def test_mark_ready_flips_draft_and_emits_event() -> None:
    pr = _open_pr()
    pr.pull_events()
    pr.mark_ready()
    events = pr.pull_events()
    assert pr.is_draft is False
    assert len(events) == 1
    assert isinstance(events[0], PRUpdated)


def test_mark_ready_idempotent() -> None:
    pr = _open_pr(is_draft=False)
    pr.pull_events()
    pr.mark_ready()
    assert pr.pull_events() == []


def test_update_body_emits_event() -> None:
    pr = _open_pr()
    pr.pull_events()
    pr.update_body("New body")
    events = pr.pull_events()
    assert pr.body == "New body"
    assert len(events) == 1
    assert isinstance(events[0], PRUpdated)


def test_update_body_idempotent_when_unchanged() -> None:
    pr = _open_pr(body="same")
    pr.pull_events()
    pr.update_body("same")
    assert pr.pull_events() == []
