"""Tests for secret_friend domain signal emission via SecretFriendService."""

from sqlalchemy.orm import Session

from src.domain.group.schemas import GroupCreate
from src.domain.group.service import GroupService
from src.domain.participant.schemas import ParticipantCreate
from src.domain.participant.service import ParticipantService
from src.domain.secret_friend.repository import SecretFriendRepository
from src.domain.secret_friend.schemas import SecretFriendLink
from src.domain.secret_friend.service import SecretFriendService
from src.domain.secret_friend.signals import (
    secret_friend_assigned,
    secret_friend_deleted,
)


def _setup_group_with_two_participants(db_session: Session):
    """Helper: create a group and two participants, return (group, p1, p2)."""
    group = GroupService.create(
        GroupCreate(name="Signal Group", description="d"), db_session
    )
    p1 = ParticipantService.create(
        ParticipantCreate(name="Alice", group_id=group.id), db_session
    )
    p2 = ParticipantService.create(
        ParticipantCreate(name="Bob", group_id=group.id), db_session
    )
    return group, p1, p2


def test_secret_friend_assigned_signal_fires_on_assign(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    group, p1, p2 = _setup_group_with_two_participants(db_session)

    secret_friend_assigned.connect(handler)
    try:
        SecretFriendService.assign(
            group_id=group.id, participant_id=p1.id, db_session=db_session
        )
        assert len(received) == 1
        assert received[0]["group_id"] == group.id
        assert received[0]["participant_id"] == p1.id
    finally:
        secret_friend_assigned.disconnect(handler)


def test_secret_friend_deleted_signal_fires_on_delete(db_session: Session) -> None:
    received: list[dict] = []

    def handler(sender: object, **kwargs: object) -> None:
        received.append(kwargs)

    group, p1, p2 = _setup_group_with_two_participants(db_session)

    # Create the link directly (no status side-effects needed here)
    assignment = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=p1.id, gift_receiver_id=p2.id),
        db_session,
    )

    secret_friend_deleted.connect(handler)
    try:
        SecretFriendService.delete(assignment.id, db_session)
        assert len(received) == 1
        assert received[0]["secret_friend_id"] == assignment.id
    finally:
        secret_friend_deleted.disconnect(handler)
