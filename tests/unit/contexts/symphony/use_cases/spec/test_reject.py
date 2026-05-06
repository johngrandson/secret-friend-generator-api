"""Unit tests for RejectSpecUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.domain.spec.events import SpecRejected
from src.contexts.symphony.use_cases.spec.dto import SpecDTO
from src.contexts.symphony.use_cases.spec.reject import RejectSpecRequest, RejectSpecUseCase
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher():
    return AsyncMock()


@pytest.fixture
def use_case(uow, publisher):
    return RejectSpecUseCase(uow=uow, event_publisher=publisher)


async def test_reject_spec_success(use_case, uow, publisher):
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.pull_events()  # drain factory event so mock update returns clean object
    uow.specs.find_by_id.return_value = spec
    uow.specs.update.return_value = spec

    resp = await use_case.execute(
        RejectSpecRequest(spec_id=spec.id, reason="Not detailed enough.")
    )

    assert resp.success is True
    assert isinstance(resp.spec, SpecDTO)
    assert resp.error_message is None
    assert uow.committed is True
    publisher.publish.assert_called_once()


async def test_reject_spec_publishes_spec_rejected_event(use_case, uow, publisher):
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.pull_events()  # drain factory event so only SpecRejected is published
    uow.specs.find_by_id.return_value = spec
    uow.specs.update.return_value = spec

    await use_case.execute(
        RejectSpecRequest(spec_id=spec.id, reason="Missing edge cases.")
    )

    events = publisher.publish.call_args[0][0]
    assert len(events) == 1
    assert isinstance(events[0], SpecRejected)
    assert events[0].reason == "Missing edge cases."


async def test_reject_spec_not_found(use_case, uow, publisher):
    uow.specs.find_by_id.return_value = None

    resp = await use_case.execute(RejectSpecRequest(spec_id=uuid4(), reason="reason"))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    uow.specs.update.assert_not_called()
    publisher.publish.assert_not_called()


async def test_reject_spec_already_decided(use_case, uow, publisher):
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.reject(reason="first rejection")
    spec.pull_events()  # clear pending events
    uow.specs.find_by_id.return_value = spec

    resp = await use_case.execute(
        RejectSpecRequest(spec_id=spec.id, reason="second rejection")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.specs.update.assert_not_called()
    publisher.publish.assert_not_called()


async def test_reject_spec_blank_reason(use_case, uow, publisher):
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    uow.specs.find_by_id.return_value = spec

    resp = await use_case.execute(RejectSpecRequest(spec_id=spec.id, reason="   "))

    assert resp.success is False
    assert resp.error_message is not None
    uow.specs.update.assert_not_called()
    publisher.publish.assert_not_called()
