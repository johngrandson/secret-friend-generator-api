"""Pydantic edge tests — model_validate(entity) traverses nested types."""

from src.api.group.schemas import GroupRead
from src.domain.group.entities import Group
from src.domain.group.value_objects import CategoryEnum, ParticipantSummary


def test_group_read_validates_from_entity_with_participants() -> None:
    entity = Group(
        id=1,
        name="Test",
        description="d",
        category=CategoryEnum.santa,
        link_url="abc",
        participants=[
            ParticipantSummary(id=10, name="Alice"),
            ParticipantSummary(id=11, name="Bob"),
        ],
    )

    dto = GroupRead.model_validate(entity)

    assert dto.id == 1
    assert dto.link_url == "abc"
    assert [p.id for p in dto.participants] == [10, 11]
    assert [p.name for p in dto.participants] == ["Alice", "Bob"]


def test_group_read_validates_from_entity_without_participants() -> None:
    entity = Group(id=2, name="Empty", description="d")
    dto = GroupRead.model_validate(entity)
    assert dto.participants == []
