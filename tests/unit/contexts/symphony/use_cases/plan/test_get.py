"""Unit tests for GetPlanUseCase."""

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.use_cases.plan.dto import PlanDTO
from src.contexts.symphony.use_cases.plan.get import GetPlanRequest, GetPlanUseCase
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def use_case(uow):
    return GetPlanUseCase(uow=uow)


async def test_get_existing_plan(use_case, uow):
    plan = Plan.create(run_id=uuid4(), version=1, content="some content")
    uow.plans.find_by_id.return_value = plan

    resp = await use_case.execute(GetPlanRequest(plan_id=plan.id))

    assert resp.success is True
    assert isinstance(resp.plan, PlanDTO)
    assert resp.plan.id == plan.id
    assert resp.plan.version == 1


async def test_get_nonexistent_plan(use_case, uow):
    uow.plans.find_by_id.return_value = None

    resp = await use_case.execute(GetPlanRequest(plan_id=uuid4()))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    assert resp.plan is None
