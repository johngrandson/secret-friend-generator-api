"""Unit tests for GetSpecUseCase."""

from uuid import uuid4

import pytest

from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.use_cases.spec.dto import SpecDTO
from src.contexts.symphony.use_cases.spec.get import GetSpecRequest, GetSpecUseCase
from tests.conftest import FakeSymphonyUoW


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def use_case(uow):
    return GetSpecUseCase(uow=uow)


async def test_get_existing_spec(use_case, uow):
    spec = Spec.create(run_id=uuid4(), version=1, content="some content")
    uow.specs.find_by_id.return_value = spec

    resp = await use_case.execute(GetSpecRequest(spec_id=spec.id))

    assert resp.success is True
    assert isinstance(resp.spec, SpecDTO)
    assert resp.spec.id == spec.id
    assert resp.spec.version == 1


async def test_get_nonexistent_spec(use_case, uow):
    uow.specs.find_by_id.return_value = None

    resp = await use_case.execute(GetSpecRequest(spec_id=uuid4()))

    assert resp.success is False
    assert "not found" in resp.error_message.lower()
    assert resp.spec is None
