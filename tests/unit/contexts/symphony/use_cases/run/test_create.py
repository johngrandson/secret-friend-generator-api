"""Unit tests for CreateRunUseCase."""

from unittest.mock import AsyncMock

import pytest

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import RunStarted
from src.contexts.symphony.use_cases.run.create import CreateRunRequest, CreateRunUseCase
from src.contexts.symphony.use_cases.run.dto import RunDTO
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(uow, publisher):
    return CreateRunUseCase(uow=uow, event_publisher=publisher)


async def test_create_run_success(use_case, uow, publisher):
    saved_run = Run.create(issue_id="issue-123")
    uow.runs.save.return_value = saved_run

    resp = await use_case.execute(CreateRunRequest(issue_id="issue-123"))

    assert resp.success is True
    assert isinstance(resp.run, RunDTO)
    assert resp.run.issue_id == "issue-123"
    assert resp.error_message is None
    assert uow.committed is True
    publisher.publish.assert_called_once()


async def test_create_run_publishes_run_started_event(use_case, uow, publisher):
    saved_run = Run.create(issue_id="issue-456")
    uow.runs.save.return_value = saved_run

    await use_case.execute(CreateRunRequest(issue_id="issue-456"))

    events = publisher.publish.call_args[0][0]
    assert len(events) == 1
    assert isinstance(events[0], RunStarted)
    assert events[0].issue_id == "issue-456"


async def test_create_run_blank_issue_id(use_case, uow, publisher):
    resp = await use_case.execute(CreateRunRequest(issue_id="   "))

    assert resp.success is False
    assert resp.error_message is not None
    uow.runs.save.assert_not_called()
    publisher.publish.assert_not_called()


async def test_create_run_status_is_string(use_case, uow, publisher):
    saved_run = Run.create(issue_id="issue-789")
    uow.runs.save.return_value = saved_run

    resp = await use_case.execute(CreateRunRequest(issue_id="issue-789"))

    assert isinstance(resp.run.status, str)
    assert resp.run.status == "received"
