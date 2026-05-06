"""Unit tests for the Plan aggregate entity."""

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.domain.plan.events import PlanApproved, PlanCreated, PlanRejected


def test_create_returns_plan_with_fields():
    run_id = uuid4()
    plan = Plan.create(run_id=run_id, version=1, content="Implement the API.")
    assert plan.run_id == run_id
    assert plan.version == 1
    assert plan.content == "Implement the API."
    assert plan.id is not None


def test_create_collects_plan_created_event():
    run_id = uuid4()
    plan = Plan.create(run_id=run_id, version=2, content="Revised plan.")
    events = plan.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], PlanCreated)
    assert events[0].plan_id == plan.id
    assert events[0].run_id == run_id
    assert events[0].version == 2


def test_create_version_zero_raises():
    with pytest.raises(ValueError):
        Plan.create(run_id=uuid4(), version=0, content="content")


def test_create_negative_version_raises():
    with pytest.raises(ValueError):
        Plan.create(run_id=uuid4(), version=-1, content="content")


def test_create_blank_content_raises():
    with pytest.raises(ValueError):
        Plan.create(run_id=uuid4(), version=1, content="   ")


def test_create_empty_content_raises():
    with pytest.raises(ValueError):
        Plan.create(run_id=uuid4(), version=1, content="")


def test_is_pending_true_initially():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    assert plan.is_pending() is True


def test_is_pending_false_after_approve():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.approve(by="reviewer-1")
    assert plan.is_pending() is False


def test_is_pending_false_after_reject():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.reject(reason="Needs more detail.")
    assert plan.is_pending() is False


def test_approve_sets_approved_by_and_approved_at():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.approve(by="alice")
    assert plan.approved_by == "alice"
    assert plan.approved_at is not None


def test_approve_collects_plan_approved_event():
    run_id = uuid4()
    plan = Plan.create(run_id=run_id, version=1, content="content")
    plan.pull_events()  # clear PlanCreated

    plan.approve(by="reviewer-1")

    events = plan.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], PlanApproved)
    assert events[0].plan_id == plan.id
    assert events[0].run_id == run_id
    assert events[0].version == 1
    assert events[0].approved_by == "reviewer-1"


def test_approve_second_time_raises_write_once():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.approve(by="first-reviewer")
    with pytest.raises(ValueError):
        plan.approve(by="second-reviewer")


def test_approve_blank_by_raises():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    with pytest.raises(ValueError):
        plan.approve(by="   ")


def test_approve_empty_by_raises():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    with pytest.raises(ValueError):
        plan.approve(by="")


def test_reject_sets_rejection_reason():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.reject(reason="Missing context.")
    assert plan.rejection_reason == "Missing context."


def test_reject_collects_plan_rejected_event():
    run_id = uuid4()
    plan = Plan.create(run_id=run_id, version=1, content="content")
    plan.pull_events()  # clear PlanCreated

    plan.reject(reason="Incomplete.")

    events = plan.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], PlanRejected)
    assert events[0].plan_id == plan.id
    assert events[0].run_id == run_id
    assert events[0].version == 1
    assert events[0].reason == "Incomplete."


def test_reject_after_approve_raises_write_once():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.approve(by="reviewer-1")
    with pytest.raises(ValueError):
        plan.reject(reason="Changed my mind.")


def test_reject_blank_reason_raises():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    with pytest.raises(ValueError):
        plan.reject(reason="   ")


def test_reject_empty_reason_raises():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    with pytest.raises(ValueError):
        plan.reject(reason="")


def test_pull_events_clears_after_read():
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.pull_events()
    assert plan.pull_events() == []
