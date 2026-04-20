from sqlalchemy.orm import Session

from src.domain.secret_friend.repository import SecretFriendRepository
from src.domain.secret_friend.schemas import SecretFriendLink


def test_link_creates_new_secret_friend_record(
    db_session: Session, participant_fixture
):
    giver = participant_fixture()
    receiver = participant_fixture()

    result = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=giver.id, gift_receiver_id=receiver.id),
        db_session,
    )
    assert result.id is not None
    assert result.gift_giver_id == giver.id
    assert result.gift_receiver_id == receiver.id


def test_link_upserts_existing_record_by_giver_id(
    db_session: Session, participant_fixture
):
    giver = participant_fixture()
    receiver_1 = participant_fixture()
    receiver_2 = participant_fixture()

    first = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=giver.id, gift_receiver_id=receiver_1.id),
        db_session,
    )
    second = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=giver.id, gift_receiver_id=receiver_2.id),
        db_session,
    )

    # Same row updated, not a new row
    assert first.id == second.id
    assert second.gift_receiver_id == receiver_2.id


def test_link_two_different_givers_creates_two_records(
    db_session: Session, participant_fixture
):
    giver_a = participant_fixture()
    giver_b = participant_fixture()
    receiver = participant_fixture()

    sf_a = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=giver_a.id, gift_receiver_id=receiver.id),
        db_session,
    )
    sf_b = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=giver_b.id, gift_receiver_id=receiver.id),
        db_session,
    )

    assert sf_a.id != sf_b.id
