import pytest
from sqlalchemy.orm import Session

from src.domain.secret_friend.repository import SecretFriendRepository
from src.domain.secret_friend.schemas import SecretFriendLink
from src.shared.exceptions import NotFoundError


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


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


def test_get_by_id_returns_secret_friend(db_session: Session, participant_fixture):
    """get_by_id returns the SecretFriend row when it exists."""
    giver = participant_fixture()
    receiver = participant_fixture()
    created = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=giver.id, gift_receiver_id=receiver.id),
        db_session,
    )

    result = SecretFriendRepository.get_by_id(created.id, db_session)

    assert result.id == created.id
    assert result.gift_giver_id == giver.id
    assert result.gift_receiver_id == receiver.id


def test_get_by_id_not_found_raises(db_session: Session):
    """get_by_id raises NotFoundError when no row matches the given id."""
    with pytest.raises(NotFoundError):
        SecretFriendRepository.get_by_id(999_999, db_session)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_removes_secret_friend(db_session: Session, participant_fixture):
    """delete() flushes the removal so the row is no longer retrievable."""
    giver = participant_fixture()
    receiver = participant_fixture()
    created = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=giver.id, gift_receiver_id=receiver.id),
        db_session,
    )
    record_id = created.id

    SecretFriendRepository.delete(record_id, db_session)

    # After flush the session cache is cleared — direct get should return None
    db_session.expire_all()
    assert db_session.get(type(created), record_id) is None


def test_delete_not_found_raises(db_session: Session):
    """delete() raises NotFoundError when no row matches the given id."""
    with pytest.raises(NotFoundError):
        SecretFriendRepository.delete(999_999, db_session)
