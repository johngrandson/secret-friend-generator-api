"""Unit tests for ListRunsUseCase."""

import pytest

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.run.list import ListRunsRequest, ListRunsUseCase
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def use_case(uow):
    return ListRunsUseCase(uow=uow)


async def test_list_returns_all_runs(use_case, uow):
    runs = [Run.create(issue_id="issue-1"), Run.create(issue_id="issue-2")]
    uow.runs.list.return_value = runs

    resp = await use_case.execute(ListRunsRequest())

    assert resp.success is True
    assert len(resp.runs) == 2
    assert all(isinstance(r, RunDTO) for r in resp.runs)
    assert resp.runs[0].issue_id == "issue-1"
    assert resp.runs[1].issue_id == "issue-2"
    uow.runs.list.assert_called_once_with(limit=20, offset=0)


async def test_list_passes_pagination(use_case, uow):
    uow.runs.list.return_value = []

    await use_case.execute(ListRunsRequest(limit=5, offset=10))

    uow.runs.list.assert_called_once_with(limit=5, offset=10)


async def test_list_empty_returns_empty_list(use_case, uow):
    uow.runs.list.return_value = []

    resp = await use_case.execute(ListRunsRequest())

    assert resp.runs == []
