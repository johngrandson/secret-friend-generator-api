"""SecretFriendService tests — signal emission + cross-domain reveal."""

import pytest
from sqlalchemy.orm import Session

from src.domain.participant.service import ParticipantService
from src.domain.participant.value_objects import ParticipantStatus
from src.domain.secret_friend.service import SecretFriendService
from src.domain.secret_friend.signals import (
    secret_friend_assigned,
    secret_friend_deleted,
)
from src.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.repositories.participant_repository import (
    PostgresParticipantRepository,
)
from src.infrastructure.repositories.secret_friend_repository import (
    PostgresSecretFriendRepository,
)
from src.shared.exceptions import BusinessRuleError


def _participant_service(db: Session) -> ParticipantService:
    return ParticipantService(
        repo=PostgresParticipantRepository(db),
        uow=SqlAlchemyUnitOfWork(db),
    )


def _service(
    db: Session, participants: ParticipantService
) -> SecretFriendService:
    return SecretFriendService(
        repo=PostgresSecretFriendRepository(db),
        participant_service=participants,
        uow=SqlAlchemyUnitOfWork(db),
    )


def _setup_two_participants(db_session, group_fixture, participant_fixture):
    group = group_fixture()
    p1 = participant_fixture(group=group, name="Alice")
    p2 = participant_fixture(group=group, name="Bob")
    return group, p1, p2


def test_assign_fires_secret_friend_assigned_signal_once(
    db_session: Session, group_fixture, participant_fixture
) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    group, p1, _ = _setup_two_participants(
        db_session, group_fixture, participant_fixture
    )
    participants = _participant_service(db_session)

    secret_friend_assigned.connect(handler)
    try:
        _service(db_session, participants).assign(
            group_id=group.id, participant_id=p1.id
        )
        assert len(received) == 1
        assert received[0]["group_id"] == group.id
        assert received[0]["participant_id"] == p1.id
        assert "db_session" not in received[0]
    finally:
        secret_friend_assigned.disconnect(handler)


def test_assign_marks_giver_as_revealed_via_inline_call(
    db_session: Session, group_fixture, participant_fixture
) -> None:
    """Cross-domain reveal: SecretFriendService.assign updates the giver's
    status by calling participant_service.update directly — no signal magic.
    """
    group, p1, _ = _setup_two_participants(
        db_session, group_fixture, participant_fixture
    )
    participants = _participant_service(db_session)

    _service(db_session, participants).assign(
        group_id=group.id, participant_id=p1.id
    )

    refreshed = participants.get_by_id(p1.id)
    assert refreshed.status == ParticipantStatus.REVEALED


def test_assign_with_one_participant_raises_business_rule_error(
    db_session: Session, group_fixture, participant_fixture
) -> None:
    group = group_fixture()
    p1 = participant_fixture(group=group, name="Solo")
    participants = _participant_service(db_session)

    with pytest.raises(BusinessRuleError):
        _service(db_session, participants).assign(
            group_id=group.id, participant_id=p1.id
        )


def test_delete_fires_secret_friend_deleted_signal(
    db_session: Session, group_fixture, participant_fixture
) -> None:
    received: list[dict] = []

    def handler(sender: object, **kw: object) -> None:
        received.append(kw)

    group, p1, _ = _setup_two_participants(
        db_session, group_fixture, participant_fixture
    )
    participants = _participant_service(db_session)
    service = _service(db_session, participants)
    sf = service.assign(group_id=group.id, participant_id=p1.id)

    secret_friend_deleted.connect(handler)
    try:
        service.delete(sf.id)
        assert len(received) == 1
        assert received[0]["secret_friend_id"] == sf.id
    finally:
        secret_friend_deleted.disconnect(handler)
