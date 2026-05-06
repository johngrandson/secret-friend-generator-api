"""Unit tests for the Spec aggregate entity."""

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.domain.spec.events import SpecApproved, SpecCreated, SpecRejected


def test_create_returns_spec_with_fields():
    run_id = uuid4()
    spec = Spec.create(run_id=run_id, version=1, content="Design the API.")
    assert spec.run_id == run_id
    assert spec.version == 1
    assert spec.content == "Design the API."
    assert spec.id is not None


def test_create_collects_spec_created_event():
    run_id = uuid4()
    spec = Spec.create(run_id=run_id, version=2, content="Revised design.")
    events = spec.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], SpecCreated)
    assert events[0].spec_id == spec.id
    assert events[0].run_id == run_id
    assert events[0].version == 2


def test_create_version_zero_raises():
    with pytest.raises(ValueError):
        Spec.create(run_id=uuid4(), version=0, content="content")


def test_create_negative_version_raises():
    with pytest.raises(ValueError):
        Spec.create(run_id=uuid4(), version=-1, content="content")


def test_create_blank_content_raises():
    with pytest.raises(ValueError):
        Spec.create(run_id=uuid4(), version=1, content="   ")


def test_create_empty_content_raises():
    with pytest.raises(ValueError):
        Spec.create(run_id=uuid4(), version=1, content="")


def test_is_pending_true_initially():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    assert spec.is_pending() is True


def test_is_pending_false_after_approve():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.approve(by="reviewer-1")
    assert spec.is_pending() is False


def test_is_pending_false_after_reject():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.reject(reason="Needs more detail.")
    assert spec.is_pending() is False


def test_approve_sets_approved_by_and_approved_at():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.approve(by="alice")
    assert spec.approved_by == "alice"
    assert spec.approved_at is not None


def test_approve_collects_spec_approved_event():
    run_id = uuid4()
    spec = Spec.create(run_id=run_id, version=1, content="content")
    spec.pull_events()  # clear SpecCreated

    spec.approve(by="reviewer-1")

    events = spec.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], SpecApproved)
    assert events[0].spec_id == spec.id
    assert events[0].run_id == run_id
    assert events[0].version == 1
    assert events[0].approved_by == "reviewer-1"


def test_approve_second_time_raises_write_once():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.approve(by="first-reviewer")
    with pytest.raises(ValueError):
        spec.approve(by="second-reviewer")


def test_approve_blank_by_raises():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    with pytest.raises(ValueError):
        spec.approve(by="   ")


def test_approve_empty_by_raises():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    with pytest.raises(ValueError):
        spec.approve(by="")


def test_reject_sets_rejection_reason():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.reject(reason="Missing context.")
    assert spec.rejection_reason == "Missing context."


def test_reject_collects_spec_rejected_event():
    run_id = uuid4()
    spec = Spec.create(run_id=run_id, version=1, content="content")
    spec.pull_events()  # clear SpecCreated

    spec.reject(reason="Incomplete.")

    events = spec.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], SpecRejected)
    assert events[0].spec_id == spec.id
    assert events[0].run_id == run_id
    assert events[0].version == 1
    assert events[0].reason == "Incomplete."


def test_reject_after_approve_raises_write_once():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.approve(by="reviewer-1")
    with pytest.raises(ValueError):
        spec.reject(reason="Changed my mind.")


def test_reject_blank_reason_raises():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    with pytest.raises(ValueError):
        spec.reject(reason="   ")


def test_reject_empty_reason_raises():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    with pytest.raises(ValueError):
        spec.reject(reason="")


def test_pull_events_clears_after_read():
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.pull_events()
    assert spec.pull_events() == []
