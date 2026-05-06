"""Unit tests for CreateSpecUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.domain.spec.events import SpecCreated
from src.contexts.symphony.use_cases.spec.create import CreateSpecRequest, CreateSpecUseCase
from src.contexts.symphony.use_cases.spec.dto import SpecDTO
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(uow, publisher):
    return CreateSpecUseCase(uow=uow, event_publisher=publisher)


async def test_create_spec_success(use_case, uow, publisher):
    run_id = uuid4()
    saved_spec = Spec.create(run_id=run_id, version=1, content="spec content")
    uow.specs.save.return_value = saved_spec

    resp = await use_case.execute(
        CreateSpecRequest(run_id=run_id, version=1, content="spec content")
    )

    assert resp.success is True
    assert isinstance(resp.spec, SpecDTO)
    assert resp.spec.run_id == run_id
    assert resp.spec.version == 1
    assert resp.error_message is None
    assert uow.committed is True
    publisher.publish.assert_called_once()


async def test_create_spec_publishes_spec_created_event(use_case, uow, publisher):
    run_id = uuid4()
    saved_spec = Spec.create(run_id=run_id, version=1, content="content")
    uow.specs.save.return_value = saved_spec

    await use_case.execute(
        CreateSpecRequest(run_id=run_id, version=1, content="content")
    )

    events = publisher.publish.call_args[0][0]
    assert len(events) == 1
    assert isinstance(events[0], SpecCreated)
    assert events[0].run_id == run_id
    assert events[0].version == 1


async def test_create_spec_invalid_version(use_case, uow, publisher):
    resp = await use_case.execute(
        CreateSpecRequest(run_id=uuid4(), version=0, content="content")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.specs.save.assert_not_called()
    publisher.publish.assert_not_called()


async def test_create_spec_blank_content(use_case, uow, publisher):
    resp = await use_case.execute(
        CreateSpecRequest(run_id=uuid4(), version=1, content="   ")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.specs.save.assert_not_called()
    publisher.publish.assert_not_called()
