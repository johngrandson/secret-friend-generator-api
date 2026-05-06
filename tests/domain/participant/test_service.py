"""Service-level tests for ParticipantService — signal emission + rollback."""

import pytest
from sqlalchemy.orm import Session

from src.domain.participant.service import ParticipantService
from src.domain.participant.signals import (
    participant_created,
    participant_deleted,
    participant_updated,
)
from src.domain.participant.value_objects import ParticipantStatus
from src.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.repositories.participant_repository import (
    PostgresParticipantRepository,
)


def _service(db: Session) -> ParticipantService:
    return ParticipantService(
        repo=PostgresParticipantRepository(db),
        uow=SqlAlchemyUnitOfWork(db),
    )


def test_create_fires_participant_created_signal(
    db_session: Session, group_fixture
) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    group = group_fixture()
    participant_created.connect(handler)
    try:
        entity = _service(db_session).create(name="Alice", group_id=group.id)
        assert len(received) == 1
        assert received[0]["participant"].id == entity.id
    finally:
        participant_created.disconnect(handler)


def test_create_signal_not_fired_when_repo_raises(
    db_session: Session,
    group_fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    participant_created.connect(handler)
    service = _service(db_session)

    def boom(_: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(service._repo, "create", boom)
    try:
        with pytest.raises(RuntimeError, match="boom"):
            service.create(name="Bob", group_id=group_fixture().id)
        assert received == []
    finally:
        participant_created.disconnect(handler)


def test_update_fires_participant_updated_signal(
    db_session: Session, group_fixture
) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    service = _service(db_session)
    group = group_fixture()
    entity = service.create(name="Carol", group_id=group.id)

    participant_updated.connect(handler)
    try:
        service.update(entity.id, status=ParticipantStatus.REVEALED)
        assert len(received) == 1
        assert received[0]["participant"].status == ParticipantStatus.REVEALED
    finally:
        participant_updated.disconnect(handler)


def test_delete_fires_participant_deleted_signal(
    db_session: Session, group_fixture
) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    service = _service(db_session)
    group = group_fixture()
    entity = service.create(name="Dave", group_id=group.id)

    participant_deleted.connect(handler)
    try:
        service.delete(entity.id)
        assert len(received) == 1
        assert received[0]["participant_id"] == entity.id
    finally:
        participant_deleted.disconnect(handler)
