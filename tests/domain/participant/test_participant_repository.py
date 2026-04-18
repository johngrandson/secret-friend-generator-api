import pytest
from sqlalchemy.orm import Session

from src.domain.participant.participant_repository import ParticipantRepository
from src.domain.participant.participant_schemas import ParticipantCreate, ParticipantUpdate, ParticipantStatus
from src.domain.shared.domain_exceptions import NotFoundError


def test_create_participant_returns_participant_with_id(db_session: Session, group_fixture):
    group = group_fixture()
    participant = ParticipantRepository.create(
        ParticipantCreate(name="Alice", group_id=group.id), db_session
    )
    assert participant.id is not None


def test_create_participant_persists_name(db_session: Session, group_fixture):
    group = group_fixture()
    participant = ParticipantRepository.create(
        ParticipantCreate(name="Bob", group_id=group.id), db_session
    )
    assert participant.name == "Bob"


def test_create_participant_with_nonexistent_group_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError, match="Group not found"):
        ParticipantRepository.create(
            ParticipantCreate(name="Ghost", group_id=99999), db_session
        )


def test_get_all_returns_a_list(db_session: Session):
    result = ParticipantRepository.get_all(db_session)
    assert isinstance(result, list)


def test_get_all_returns_all_participants(db_session: Session, group_fixture):
    before = len(ParticipantRepository.get_all(db_session))
    group = group_fixture()
    ParticipantRepository.create(ParticipantCreate(name="P1", group_id=group.id), db_session)
    ParticipantRepository.create(ParticipantCreate(name="P2", group_id=group.id), db_session)
    result = ParticipantRepository.get_all(db_session)
    assert len(result) == before + 2


def test_get_by_group_id_returns_participants_for_group(db_session: Session, group_fixture):
    group = group_fixture()
    ParticipantRepository.create(ParticipantCreate(name="PA", group_id=group.id), db_session)
    ParticipantRepository.create(ParticipantCreate(name="PB", group_id=group.id), db_session)
    result = ParticipantRepository.get_by_group_id(group_id=group.id, db_session=db_session)
    assert len(result) == 2


def test_get_by_group_id_excludes_other_groups(db_session: Session, group_fixture):
    group_a = group_fixture(name="Group AAAA")
    group_b = group_fixture(name="Group BBBB")
    ParticipantRepository.create(ParticipantCreate(name="OnlyA", group_id=group_a.id), db_session)
    result = ParticipantRepository.get_by_group_id(group_id=group_b.id, db_session=db_session)
    assert result == []


def test_get_by_id_returns_correct_participant(db_session: Session, group_fixture):
    group = group_fixture()
    participant = ParticipantRepository.create(
        ParticipantCreate(name="FindMe", group_id=group.id), db_session
    )
    fetched = ParticipantRepository.get_by_id(
        participant_id=participant.id, db_session=db_session
    )
    assert fetched.id == participant.id
    assert fetched.name == "FindMe"


def test_get_by_id_nonexistent_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError, match="Participant not found"):
        ParticipantRepository.get_by_id(participant_id=99999, db_session=db_session)


def test_update_participant_name(db_session: Session, group_fixture):
    group = group_fixture()
    participant = ParticipantRepository.create(
        ParticipantCreate(name="Old Name", group_id=group.id), db_session
    )
    updated = ParticipantRepository.update(
        participant_id=participant.id,
        payload=ParticipantUpdate(name="New Name"),
        db_session=db_session,
    )
    assert updated.name == "New Name"


def test_update_participant_gift_hint(db_session: Session, group_fixture):
    group = group_fixture()
    participant = ParticipantRepository.create(
        ParticipantCreate(name="Hinter", group_id=group.id), db_session
    )
    updated = ParticipantRepository.update(
        participant_id=participant.id,
        payload=ParticipantUpdate(gift_hint="A nice book"),
        db_session=db_session,
    )
    assert updated.gift_hint == "A nice book"


def test_update_participant_status(db_session: Session, group_fixture):
    group = group_fixture()
    participant = ParticipantRepository.create(
        ParticipantCreate(name="Status Changer", group_id=group.id), db_session
    )
    updated = ParticipantRepository.update(
        participant_id=participant.id,
        payload=ParticipantUpdate(status=ParticipantStatus.REVEALED),
        db_session=db_session,
    )
    assert updated.status == ParticipantStatus.REVEALED


def test_update_nonexistent_participant_raises_not_found(db_session: Session):
    with pytest.raises(NotFoundError, match="Participant not found"):
        ParticipantRepository.update(
            participant_id=99999,
            payload=ParticipantUpdate(name="Nobody"),
            db_session=db_session,
        )
