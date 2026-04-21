import pytest
from pydantic import ValidationError

from src.domain.secret_friend.schemas import SecretFriendLink, SecretFriendRead


# ── SecretFriendLink ──────────────────────────────────────────────────────────


def test_secret_friend_link_valid_distinct_ids_parses():
    schema = SecretFriendLink(gift_giver_id=1, gift_receiver_id=2)
    assert schema.gift_giver_id == 1
    assert schema.gift_receiver_id == 2


def test_secret_friend_link_same_ids_raises():
    with pytest.raises(ValidationError, match="same person"):
        SecretFriendLink(gift_giver_id=5, gift_receiver_id=5)


def test_secret_friend_link_giver_id_must_be_positive():
    with pytest.raises(ValidationError):
        SecretFriendLink(gift_giver_id=0, gift_receiver_id=2)


def test_secret_friend_link_receiver_id_must_be_positive():
    with pytest.raises(ValidationError):
        SecretFriendLink(gift_giver_id=1, gift_receiver_id=0)


def test_secret_friend_link_negative_giver_id_raises():
    with pytest.raises(ValidationError):
        SecretFriendLink(gift_giver_id=-1, gift_receiver_id=2)


def test_secret_friend_link_missing_giver_raises():
    with pytest.raises(ValidationError):
        SecretFriendLink(gift_receiver_id=2)


def test_secret_friend_link_missing_receiver_raises():
    with pytest.raises(ValidationError):
        SecretFriendLink(gift_giver_id=1)


# ── SecretFriendRead ──────────────────────────────────────────────────────────


def test_secret_friend_read_parses_all_fields():
    schema = SecretFriendRead(id=10, gift_giver_id=1, gift_receiver_id=2)
    assert schema.id == 10
    assert schema.gift_giver_id == 1
    assert schema.gift_receiver_id == 2


def test_secret_friend_read_missing_id_raises():
    with pytest.raises(ValidationError):
        SecretFriendRead(gift_giver_id=1, gift_receiver_id=2)
