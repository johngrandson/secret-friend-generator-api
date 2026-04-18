import pytest
from pydantic import ValidationError

from src.domain.group.group_schemas import CategoryEnum, GroupCreate, GroupRead, GroupList


# ── CategoryEnum ──────────────────────────────────────────────────────────────

def test_category_enum_has_expected_values():
    values = {e.value for e in CategoryEnum}
    assert values == {"santa", "chocolate", "frenemy", "book", "wine", "easter"}


def test_category_enum_is_string_subclass():
    assert isinstance(CategoryEnum.santa, str)


# ── GroupCreate ───────────────────────────────────────────────────────────────

def test_group_create_valid_data_parses():
    schema = GroupCreate(name="Book Club", description="Monthly reads")
    assert schema.name == "Book Club"
    assert schema.description == "Monthly reads"


def test_group_create_defaults_category_to_santa():
    schema = GroupCreate(name="My Group", description="desc")
    assert schema.category == CategoryEnum.santa


def test_group_create_accepts_explicit_category():
    schema = GroupCreate(name="Wine Night", description="desc", category=CategoryEnum.wine)
    assert schema.category == CategoryEnum.wine


def test_group_create_name_too_short_raises():
    with pytest.raises(ValidationError):
        GroupCreate(name="AB", description="desc")


def test_group_create_name_exactly_4_chars_passes():
    schema = GroupCreate(name="ABCD", description="desc")
    assert schema.name == "ABCD"


def test_group_create_name_missing_raises():
    with pytest.raises(ValidationError):
        GroupCreate(description="desc")


def test_group_create_invalid_category_raises():
    with pytest.raises(ValidationError):
        GroupCreate(name="My Group", description="desc", category="invalid")


# ── GroupRead ─────────────────────────────────────────────────────────────────

def test_group_read_participants_defaults_to_empty_list():
    schema = GroupRead(
        id=1, name="Test", description="desc",
        category=CategoryEnum.santa, link_url=None
    )
    assert schema.participants == []


def test_group_read_link_url_optional():
    schema = GroupRead(
        id=1, name="Test", description="desc",
        category=CategoryEnum.santa
    )
    assert schema.link_url is None


# ── GroupList ─────────────────────────────────────────────────────────────────

def test_group_list_defaults_to_empty():
    schema = GroupList()
    assert schema.groups == []


def test_group_list_accepts_group_read_items():
    item = GroupRead(
        id=1, name="Test", description="desc",
        category=CategoryEnum.santa, link_url="abc"
    )
    schema = GroupList(groups=[item])
    assert len(schema.groups) == 1
