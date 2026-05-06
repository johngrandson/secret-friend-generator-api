"""Unit tests for ListSpecsForRunUseCase."""

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.use_cases.spec.dto import SpecDTO
from src.contexts.symphony.use_cases.spec.list_for_run import (
    ListSpecsForRunRequest,
    ListSpecsForRunUseCase,
)
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def use_case(uow):
    return ListSpecsForRunUseCase(uow=uow)


async def test_list_specs_for_run_returns_all(use_case, uow):
    run_id = uuid4()
    specs = [
        Spec.create(run_id=run_id, version=1, content="v1 content"),
        Spec.create(run_id=run_id, version=2, content="v2 content"),
    ]
    uow.specs.list_by_run.return_value = specs

    resp = await use_case.execute(ListSpecsForRunRequest(run_id=run_id))

    assert resp.success is True
    assert len(resp.specs) == 2
    assert all(isinstance(s, SpecDTO) for s in resp.specs)
    assert resp.specs[0].version == 1
    assert resp.specs[1].version == 2
    uow.specs.list_by_run.assert_called_once_with(run_id)


async def test_list_specs_for_run_empty(use_case, uow):
    uow.specs.list_by_run.return_value = []

    resp = await use_case.execute(ListSpecsForRunRequest(run_id=uuid4()))

    assert resp.specs == []
    assert resp.success is True
