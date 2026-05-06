"""Service-level tests for GroupService — signal emission + rollback semantics."""

import pytest
from sqlalchemy.orm import Session

from src.domain.group.service import GroupService
from src.domain.group.signals import (
    group_created,
    group_deleted,
    group_updated,
)
from src.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.repositories.group_repository import (
    PostgresGroupRepository,
)


def _service(db: Session) -> GroupService:
    return GroupService(
        repo=PostgresGroupRepository(db), uow=SqlAlchemyUnitOfWork(db)
    )


def test_create_fires_group_created_signal_once(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    group_created.connect(handler)
    try:
        entity = _service(db_session).create(name="Alpha", description="d")
        assert len(received) == 1
        assert received[0]["group"].id == entity.id
    finally:
        group_created.disconnect(handler)


def test_create_signal_not_fired_when_repo_raises(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    group_created.connect(handler)
    service = _service(db_session)

    def boom(_: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(service._repo, "create", boom)
    try:
        with pytest.raises(RuntimeError, match="boom"):
            service.create(name="Beta", description="d")
        assert received == []
    finally:
        group_created.disconnect(handler)


def test_update_fires_group_updated_signal(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    service = _service(db_session)
    entity = service.create(name="Gamma", description="d")

    group_updated.connect(handler)
    try:
        service.update(entity.id, name="Gamma2")
        assert len(received) == 1
        assert received[0]["group"].name == "Gamma2"
    finally:
        group_updated.disconnect(handler)


def test_delete_fires_group_deleted_signal(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    service = _service(db_session)
    entity = service.create(name="Delta", description="d")

    group_deleted.connect(handler)
    try:
        service.delete(entity.id)
        assert len(received) == 1
        assert received[0]["group_id"] == entity.id
    finally:
        group_deleted.disconnect(handler)
