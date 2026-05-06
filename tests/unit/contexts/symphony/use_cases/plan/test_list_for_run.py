"""Unit tests for ListPlansForRunUseCase."""

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.use_cases.plan.dto import PlanDTO
from src.contexts.symphony.use_cases.plan.list_for_run import (
    ListPlansForRunRequest,
    ListPlansForRunUseCase,
)
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def use_case(uow):
    return ListPlansForRunUseCase(uow=uow)


async def test_list_plans_for_run_returns_all(use_case, uow):
    run_id = uuid4()
    plans = [
        Plan.create(run_id=run_id, version=1, content="v1 content"),
        Plan.create(run_id=run_id, version=2, content="v2 content"),
    ]
    uow.plans.list_by_run.return_value = plans

    resp = await use_case.execute(ListPlansForRunRequest(run_id=run_id))

    assert resp.success is True
    assert len(resp.plans) == 2
    assert all(isinstance(p, PlanDTO) for p in resp.plans)
    assert resp.plans[0].version == 1
    assert resp.plans[1].version == 2
    uow.plans.list_by_run.assert_called_once_with(run_id)


async def test_list_plans_for_run_empty(use_case, uow):
    uow.plans.list_by_run.return_value = []

    resp = await use_case.execute(ListPlansForRunRequest(run_id=uuid4()))

    assert resp.plans == []
    assert resp.success is True
