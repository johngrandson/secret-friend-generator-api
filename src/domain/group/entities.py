"""Group aggregate root — pure domain entity, identity-based equality."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.group.value_objects import CategoryEnum, ParticipantSummary


@dataclass
class Group:
    name: str
    description: str
    id: int | None = None
    link_url: str | None = None
    category: CategoryEnum = CategoryEnum.santa
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime | None = None
    participants: list[ParticipantSummary] = field(default_factory=list)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Group):
            return False
        return self.id is not None and self.id == other.id

    def __hash__(self) -> int:
        return hash(("Group", self.id))
