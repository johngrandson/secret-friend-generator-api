import pytest
from pydantic import ValidationError

from src.domain.participant.participant_schemas import (
    ParticipantStatus,
    ParticipantBase,
    ParticipantCreate,
    ParticipantRead,
    ParticipantUpdate,
)


# ── ParticipantStatus ─────────────────────────────────────────────────────────

def test_participant_status_has_pending_and_revealed():
    assert ParticipantStatus.PENDING == "PENDING"
    assert ParticipantStatus.REVEALED == "REVEALED"


def test_participant_status_is_string_subclass():
    assert isinstance(ParticipantStatus.PENDING, str)


# ── ParticipantBase ───────────────────────────────────────────────────────────

def test_participant_base_parses_id_and_name():
    schema = ParticipantBase(id=1, name="Alice")
    assert schema.id == 1
    assert schema.name == "Alice"


def test_participant_base_missing_id_raises():
    with pytest.raises(ValidationError):
        ParticipantBase(name="Alice")


# ── ParticipantCreate ─────────────────────────────────────────────────────────

def test_participant_create_valid_data_parses():
    schema = ParticipantCreate(name="Bob", group_id=1)
    assert schema.name == "Bob"
    assert schema.group_id == 1


def test_participant_create_missing_group_id_raises():
    with pytest.raises(ValidationError):
        ParticipantCreate(name="Bob")


def test_participant_create_missing_name_raises():
    with pytest.raises(ValidationError):
        ParticipantCreate(group_id=1)


# ── ParticipantRead ───────────────────────────────────────────────────────────

def test_participant_read_default_status_is_pending():
    from datetime import datetime
    schema = ParticipantRead(
        id=1, name="Carol", group_id=2,
        created_at=datetime.now()
    )
    assert schema.status == ParticipantStatus.PENDING


def test_participant_read_gift_hint_optional():
    from datetime import datetime
    schema = ParticipantRead(
        id=1, name="Carol", group_id=2,
        created_at=datetime.now()
    )
    assert schema.gift_hint is None


def test_participant_read_updated_at_optional():
    from datetime import datetime
    schema = ParticipantRead(
        id=1, name="Carol", group_id=2,
        created_at=datetime.now()
    )
    assert schema.updated_at is None


# ── ParticipantUpdate ─────────────────────────────────────────────────────────

def test_participant_update_with_name_only_is_valid():
    schema = ParticipantUpdate(name="New Name")
    assert schema.name == "New Name"


def test_participant_update_with_gift_hint_only_is_valid():
    schema = ParticipantUpdate(gift_hint="A book")
    assert schema.gift_hint == "A book"


def test_participant_update_with_status_only_is_valid():
    schema = ParticipantUpdate(status=ParticipantStatus.REVEALED)
    assert schema.status == ParticipantStatus.REVEALED


def test_participant_update_all_none_values_raises():
    with pytest.raises(ValidationError):
        ParticipantUpdate(name=None, gift_hint=None, status=None)


def test_participant_update_empty_dict_raises():
    with pytest.raises(ValidationError):
        ParticipantUpdate()
