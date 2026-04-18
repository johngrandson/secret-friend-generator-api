import pytest
from sqlalchemy.orm import Session

from src.domain.participant.participant_service import ParticipantService
from src.domain.participant.participant_schemas import (
    ParticipantCreate,
    ParticipantList,
    ParticipantRead,
    ParticipantUpdate,
    ParticipantStatus,
)
from src.domain.shared.domain_exceptions import NotFoundError


def test_create_returns_participant_read_schema(db_session: Session, group_fixture):
    group = group_fixture()
    result = ParticipantService.create(
        ParticipantCreate(name="Alice", group_id=group.id), db_session
    )
    assert isinstance(result, ParticipantRead)


def test_create_participant_sets_correct_name(db_session: Session, group_fixture):
    group = group_fixture()
    result = ParticipantService.create(
        ParticipantCreate(name="Bob", group_id=group.id), db_session
    )
    assert result.name == "Bob"


def test_create_participant_with_invalid_group_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError):
        ParticipantService.create(
            ParticipantCreate(name="Ghost", group_id=99999), db_session
        )


def test_get_all_returns_participant_list_schema(db_session: Session):
    result = ParticipantService.get_all(db_session)
    assert isinstance(result, ParticipantList)


def test_get_all_includes_created_participants(db_session: Session, group_fixture):
    before = len(ParticipantService.get_all(db_session).participants)
    group = group_fixture()
    ParticipantService.create(ParticipantCreate(name="P1", group_id=group.id), db_session)
    ParticipantService.create(ParticipantCreate(name="P2", group_id=group.id), db_session)
    result = ParticipantService.get_all(db_session)
    assert len(result.participants) == before + 2


def test_get_by_group_id_returns_list_for_group(db_session: Session, group_fixture):
    group = group_fixture()
    ParticipantService.create(ParticipantCreate(name="PA", group_id=group.id), db_session)
    result = ParticipantService.get_by_group_id(group_id=group.id, db_session=db_session)
    assert len(result) == 1
    assert isinstance(result[0], ParticipantRead)


def test_get_by_group_id_empty_for_unknown_group(db_session: Session):
    result = ParticipantService.get_by_group_id(group_id=99999, db_session=db_session)
    assert result == []


def test_get_by_id_returns_correct_participant(db_session: Session, group_fixture):
    group = group_fixture()
    created = ParticipantService.create(
        ParticipantCreate(name="FindMe", group_id=group.id), db_session
    )
    fetched = ParticipantService.get_by_id(
        participant_id=created.id, db_session=db_session
    )
    assert fetched.id == created.id
    assert isinstance(fetched, ParticipantRead)


def test_get_by_id_nonexistent_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError):
        ParticipantService.get_by_id(participant_id=99999, db_session=db_session)


def test_update_returns_participant_read_schema(db_session: Session, group_fixture):
    group = group_fixture()
    created = ParticipantService.create(
        ParticipantCreate(name="Original", group_id=group.id), db_session
    )
    result = ParticipantService.update(
        participant_id=created.id,
        payload=ParticipantUpdate(name="Updated"),
        db_session=db_session,
    )
    assert isinstance(result, ParticipantRead)
    assert result.name == "Updated"


def test_update_status_to_revealed(db_session: Session, group_fixture):
    group = group_fixture()
    created = ParticipantService.create(
        ParticipantCreate(name="Revealer", group_id=group.id), db_session
    )
    result = ParticipantService.update(
        participant_id=created.id,
        payload=ParticipantUpdate(status=ParticipantStatus.REVEALED),
        db_session=db_session,
    )
    assert result.status == ParticipantStatus.REVEALED


def test_update_nonexistent_participant_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError):
        ParticipantService.update(
            participant_id=99999,
            payload=ParticipantUpdate(name="Nobody"),
            db_session=db_session,
        )
