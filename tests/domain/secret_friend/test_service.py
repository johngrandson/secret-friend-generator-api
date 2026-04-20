import pytest
from sqlalchemy.orm import Session

from src.domain.secret_friend.service import SecretFriendService
from src.domain.secret_friend.schemas import SecretFriendLink, SecretFriendRead
from src.domain.participant.schemas import ParticipantRead, ParticipantStatus
from src.shared.exceptions import BusinessRuleError
from datetime import datetime


def _make_participant_read(id: int, group_id: int = 1) -> ParticipantRead:
    return ParticipantRead(
        id=id,
        name=f"Participant {id}",
        group_id=group_id,
        status=ParticipantStatus.PENDING,
        created_at=datetime.now(),
    )


# ── sort_secret_friends ───────────────────────────────────────────────────────

def test_sort_secret_friends_raises_with_fewer_than_two_participants():
    participant = _make_participant_read(1)
    with pytest.raises(BusinessRuleError, match="At least 2 participants"):
        SecretFriendService.sort_secret_friends(
            participant=participant, participants=[participant]
        )


def test_sort_secret_friends_raises_with_empty_list():
    participant = _make_participant_read(1)
    with pytest.raises(BusinessRuleError, match="At least 2 participants"):
        SecretFriendService.sort_secret_friends(
            participant=participant, participants=[]
        )


def test_sort_secret_friends_returns_secret_friend_link():
    giver = _make_participant_read(1)
    receiver = _make_participant_read(2)
    result = SecretFriendService.sort_secret_friends(
        participant=giver, participants=[giver, receiver]
    )
    assert isinstance(result, SecretFriendLink)


def test_sort_secret_friends_does_not_assign_self_as_receiver():
    giver = _make_participant_read(1)
    others = [_make_participant_read(i) for i in range(2, 6)]
    all_participants = [giver] + others

    for _ in range(20):  # run multiple times to cover random shuffling
        result = SecretFriendService.sort_secret_friends(
            participant=giver, participants=all_participants
        )
        assert result.gift_receiver_id != giver.id


def test_sort_secret_friends_giver_id_matches_participant(db_session: Session):
    giver = _make_participant_read(7)
    receiver = _make_participant_read(8)
    result = SecretFriendService.sort_secret_friends(
        participant=giver, participants=[giver, receiver]
    )
    assert result.gift_giver_id == giver.id


def test_sort_secret_friends_with_two_participants_links_to_the_other():
    p1 = _make_participant_read(1)
    p2 = _make_participant_read(2)
    result = SecretFriendService.sort_secret_friends(
        participant=p1, participants=[p1, p2]
    )
    assert result.gift_receiver_id == p2.id


# ── link ──────────────────────────────────────────────────────────────────────

def test_link_returns_secret_friend_read_schema(db_session: Session, participant_fixture):
    giver = participant_fixture()
    receiver = participant_fixture()

    result = SecretFriendService.link(
        secret_friend=SecretFriendLink(
            gift_giver_id=giver.id, gift_receiver_id=receiver.id
        ),
        db_session=db_session,
    )
    assert isinstance(result, SecretFriendRead)


def test_link_returns_correct_giver_and_receiver_ids(db_session: Session, participant_fixture):
    giver = participant_fixture()
    receiver = participant_fixture()

    result = SecretFriendService.link(
        secret_friend=SecretFriendLink(
            gift_giver_id=giver.id, gift_receiver_id=receiver.id
        ),
        db_session=db_session,
    )
    assert result.gift_giver_id == giver.id
    assert result.gift_receiver_id == receiver.id
