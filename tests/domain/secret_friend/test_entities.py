"""SecretFriend invariant tests — enforced on creation, not hydration."""

import pytest

from src.domain.secret_friend.entities import SecretFriend


def test_create_rejects_giver_equal_to_receiver() -> None:
    with pytest.raises(ValueError, match="cannot be the same"):
        SecretFriend.create(gift_giver_id=1, gift_receiver_id=1)


def test_create_accepts_distinct_ids() -> None:
    sf = SecretFriend.create(gift_giver_id=1, gift_receiver_id=2)
    assert sf.gift_giver_id == 1
    assert sf.gift_receiver_id == 2


def test_bare_constructor_does_not_validate_for_hydration_path() -> None:
    """Repos rebuild entities from rows via the bare ctor; corrupt data
    must not raise during a read so callers can surface domain errors
    contextually (e.g. ConflictError) rather than 500s."""
    sf = SecretFriend(gift_giver_id=1, gift_receiver_id=1, id=42)
    assert sf.id == 42
