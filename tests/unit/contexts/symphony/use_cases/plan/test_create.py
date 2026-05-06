"""Unit tests for CreatePlanUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.domain.plan.events import PlanCreated
from src.contexts.symphony.use_cases.plan.create import CreatePlanRequest, CreatePlanUseCase
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
    return CreatePlanUseCase(uow=uow, event_publisher=publisher)


async def test_create_plan_success(use_case, uow, publisher):
    run_id = uuid4()
    saved_plan = Plan.create(run_id=run_id, version=1, content="plan content")
    uow.plans.save.return_value = saved_plan

    resp = await use_case.execute(
        CreatePlanRequest(run_id=run_id, version=1, content="plan content")
    )

    assert resp.success is True
    assert isinstance(resp.plan, PlanDTO)
    assert resp.plan.run_id == run_id
    assert resp.plan.version == 1
    assert resp.error_message is None
    assert uow.committed is True
    publisher.publish.assert_called_once()


async def test_create_plan_publishes_plan_created_event(use_case, uow, publisher):
    run_id = uuid4()
    saved_plan = Plan.create(run_id=run_id, version=1, content="content")
    uow.plans.save.return_value = saved_plan

    await use_case.execute(
        CreatePlanRequest(run_id=run_id, version=1, content="content")
    )

    events = publisher.publish.call_args[0][0]
    assert len(events) == 1
    assert isinstance(events[0], PlanCreated)
    assert events[0].run_id == run_id
    assert events[0].version == 1


async def test_create_plan_invalid_version(use_case, uow, publisher):
    resp = await use_case.execute(
        CreatePlanRequest(run_id=uuid4(), version=0, content="content")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.plans.save.assert_not_called()
    publisher.publish.assert_not_called()


async def test_create_plan_blank_content(use_case, uow, publisher):
    resp = await use_case.execute(
        CreatePlanRequest(run_id=uuid4(), version=1, content="   ")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.plans.save.assert_not_called()
    publisher.publish.assert_not_called()
