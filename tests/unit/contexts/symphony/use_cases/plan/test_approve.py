"""Unit tests for ApprovePlanUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.domain.plan.events import PlanApproved
from src.contexts.symphony.use_cases.plan.approve import ApprovePlanRequest, ApprovePlanUseCase
from src.contexts.symphony.use_cases.plan.dto import PlanDTO
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(uow, publisher):
    return ApprovePlanUseCase(uow=uow, event_publisher=publisher)


async def test_approve_plan_success(use_case, uow, publisher):
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.pull_events()  # drain factory event so mock update returns clean object
    uow.plans.find_by_id.return_value = plan
    uow.plans.update.return_value = plan

    resp = await use_case.execute(
        ApprovePlanRequest(plan_id=plan.id, approved_by="reviewer-1")
    )

    assert resp.success is True
    assert isinstance(resp.plan, PlanDTO)
    assert resp.error_message is None
    assert uow.committed is True
    publisher.publish.assert_called_once()


async def test_approve_plan_publishes_plan_approved_event(use_case, uow, publisher):
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.pull_events()  # drain factory event so only PlanApproved is published
    uow.plans.find_by_id.return_value = plan
    uow.plans.update.return_value = plan

    await use_case.execute(
        ApprovePlanRequest(plan_id=plan.id, approved_by="reviewer-1")
    )

    events = publisher.publish.call_args[0][0]
    assert len(events) == 1
    assert isinstance(events[0], PlanApproved)
    assert events[0].approved_by == "reviewer-1"


async def test_approve_plan_not_found(use_case, uow, publisher):
    uow.plans.find_by_id.return_value = None

    resp = await use_case.execute(
        ApprovePlanRequest(plan_id=uuid4(), approved_by="reviewer-1")
    )

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    uow.plans.update.assert_not_called()
    publisher.publish.assert_not_called()


async def test_approve_plan_already_decided(use_case, uow, publisher):
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    plan.approve(by="first-reviewer")
    plan.pull_events()  # clear pending events
    uow.plans.find_by_id.return_value = plan

    resp = await use_case.execute(
        ApprovePlanRequest(plan_id=plan.id, approved_by="second-reviewer")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.plans.update.assert_not_called()
    publisher.publish.assert_not_called()


async def test_approve_plan_blank_approver(use_case, uow, publisher):
    plan = Plan.create(run_id=uuid4(), version=1, content="content")
    uow.plans.find_by_id.return_value = plan

    resp = await use_case.execute(
        ApprovePlanRequest(plan_id=plan.id, approved_by="   ")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.plans.update.assert_not_called()
    publisher.publish.assert_not_called()
