"""Participant aggregate root — pure domain entity, identity-based equality."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.participant.value_objects import ParticipantStatus


@dataclass
class Participant:
    name: str
    group_id: int
    id: int | None = None
    gift_hint: str | None = None
    status: ParticipantStatus = ParticipantStatus.PENDING
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Participant):
            return False
        return self.id is not None and self.id == other.id

    def __hash__(self) -> int:
        return hash(("Participant", self.id))
