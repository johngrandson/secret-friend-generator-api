"""Unit tests for GetRunUseCase."""

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.run.get import GetRunRequest, GetRunUseCase
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def use_case(uow):
    return GetRunUseCase(uow=uow)


async def test_get_existing_run(use_case, uow):
    run = Run.create(issue_id="issue-abc")
    uow.runs.find_by_id.return_value = run

    resp = await use_case.execute(GetRunRequest(run_id=run.id))

    assert resp.success is True
    assert isinstance(resp.run, RunDTO)
    assert resp.run.id == run.id
    assert resp.run.issue_id == "issue-abc"


async def test_get_nonexistent_run(use_case, uow):
    uow.runs.find_by_id.return_value = None

    resp = await use_case.execute(GetRunRequest(run_id=uuid4()))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    assert resp.run is None
