"""Participant output port — repository Protocol (driven side of hexagon)."""

from typing import Protocol

from src.domain.participant.entities import Participant
from src.domain.participant.value_objects import ParticipantStatus


class IParticipantRepository(Protocol):
    def create(self, participant: Participant) -> Participant: ...
    def get_all(self) -> list[Participant]: ...
    def get_by_id(self, participant_id: int) -> Participant: ...
    def get_by_group_id(self, group_id: int) -> list[Participant]: ...
    def update(
        self,
        participant_id: int,
        *,
        name: str | None = None,
        gift_hint: str | None = None,
        status: ParticipantStatus | None = None,
    ) -> Participant: ...
    def delete(self, participant_id: int) -> None: ...
