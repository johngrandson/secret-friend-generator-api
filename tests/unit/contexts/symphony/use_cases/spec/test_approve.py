"""Unit tests for ApproveSpecUseCase."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.domain.spec.events import SpecApproved
from src.contexts.symphony.use_cases.spec.approve import ApproveSpecRequest, ApproveSpecUseCase
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
    return ApproveSpecUseCase(uow=uow, event_publisher=publisher)


async def test_approve_spec_success(use_case, uow, publisher):
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.pull_events()  # drain factory event so mock update returns clean object
    uow.specs.find_by_id.return_value = spec
    uow.specs.update.return_value = spec

    resp = await use_case.execute(
        ApproveSpecRequest(spec_id=spec.id, approved_by="reviewer-1")
    )

    assert resp.success is True
    assert isinstance(resp.spec, SpecDTO)
    assert resp.error_message is None
    assert uow.committed is True
    publisher.publish.assert_called_once()


async def test_approve_spec_publishes_spec_approved_event(use_case, uow, publisher):
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.pull_events()  # drain factory event so only SpecApproved is published
    uow.specs.find_by_id.return_value = spec
    uow.specs.update.return_value = spec

    await use_case.execute(
        ApproveSpecRequest(spec_id=spec.id, approved_by="reviewer-1")
    )

    events = publisher.publish.call_args[0][0]
    assert len(events) == 1
    assert isinstance(events[0], SpecApproved)
    assert events[0].approved_by == "reviewer-1"


async def test_approve_spec_not_found(use_case, uow, publisher):
    uow.specs.find_by_id.return_value = None

    resp = await use_case.execute(
        ApproveSpecRequest(spec_id=uuid4(), approved_by="reviewer-1")
    )

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    uow.specs.update.assert_not_called()
    publisher.publish.assert_not_called()


async def test_approve_spec_already_decided(use_case, uow, publisher):
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    spec.approve(by="first-reviewer")
    spec.pull_events()  # clear pending events
    uow.specs.find_by_id.return_value = spec

    resp = await use_case.execute(
        ApproveSpecRequest(spec_id=spec.id, approved_by="second-reviewer")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.specs.update.assert_not_called()
    publisher.publish.assert_not_called()


async def test_approve_spec_blank_approver(use_case, uow, publisher):
    spec = Spec.create(run_id=uuid4(), version=1, content="content")
    uow.specs.find_by_id.return_value = spec

    resp = await use_case.execute(
        ApproveSpecRequest(spec_id=spec.id, approved_by="   ")
    )

    assert resp.success is False
    assert resp.error_message is not None
    uow.specs.update.assert_not_called()
    publisher.publish.assert_not_called()
