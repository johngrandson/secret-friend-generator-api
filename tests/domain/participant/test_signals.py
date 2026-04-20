"""Tests for participant domain signal emission via ParticipantService."""

from sqlalchemy.orm import Session

from src.domain.group.schemas import GroupCreate
from src.domain.group.service import GroupService
from src.domain.participant.schemas import ParticipantCreate, ParticipantUpdate
from src.domain.participant.service import ParticipantService
from src.domain.participant.signals import (
    participant_created,
    participant_deleted,
    participant_updated,
)


def test_participant_created_signal_fires_on_create(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    group = GroupService.create(GroupCreate(name="Test Group", description="d"), db_session)

    participant_created.connect(handler)
    try:
        ParticipantService.create(
            ParticipantCreate(name="Alice", group_id=group.id), db_session
        )
        assert len(received) == 1
        assert received[0]["participant"].name == "Alice"
    finally:
        participant_created.disconnect(handler)


def test_participant_updated_signal_fires_on_update(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    group = GroupService.create(GroupCreate(name="Test Group", description="d"), db_session)
    participant = ParticipantService.create(
        ParticipantCreate(name="Bob", group_id=group.id), db_session
    )

    participant_updated.connect(handler)
    try:
        ParticipantService.update(
            participant.id, ParticipantUpdate(name="Bobby"), db_session
        )
        assert len(received) == 1
        assert received[0]["participant"].name == "Bobby"
    finally:
        participant_updated.disconnect(handler)


def test_participant_deleted_signal_fires_on_delete(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    group = GroupService.create(GroupCreate(name="Test Group", description="d"), db_session)
    participant = ParticipantService.create(
        ParticipantCreate(name="Carol", group_id=group.id), db_session
    )

    participant_deleted.connect(handler)
    try:
        ParticipantService.delete(participant.id, db_session)
        assert len(received) == 1
        assert received[0]["participant_id"] == participant.id
    finally:
        participant_deleted.disconnect(handler)
