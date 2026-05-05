"""Participant use cases — depend on Protocol, operate on domain entities."""

from sqlalchemy.orm import Session

from src.domain.participant.entities import Participant
from src.domain.participant.repositories import IParticipantRepository
from src.domain.participant.signals import (
    participant_created,
    participant_deleted,
    participant_updated,
)
from src.domain.participant.value_objects import ParticipantStatus
from src.infrastructure.persistence import transaction


class ParticipantService:
    def __init__(self, repo: IParticipantRepository, db: Session) -> None:
        self._repo = repo
        self._db = db

    def create(self, *, name: str, group_id: int) -> Participant:
        with transaction(self._db):
            entity = self._repo.create(Participant(name=name, group_id=group_id))
            participant_created.send(self.__class__, participant=entity)
            return entity

    def get_all(self) -> list[Participant]:
        return self._repo.get_all()

    def get_by_id(self, participant_id: int) -> Participant:
        return self._repo.get_by_id(participant_id)

    def get_by_group_id(self, group_id: int) -> list[Participant]:
        return self._repo.get_by_group_id(group_id)

    def update(
        self,
        participant_id: int,
        *,
        name: str | None = None,
        gift_hint: str | None = None,
        status: ParticipantStatus | None = None,
    ) -> Participant:
        fields = {
            k: v
            for k, v in {
                "name": name,
                "gift_hint": gift_hint,
                "status": status,
            }.items()
            if v is not None
        }
        with transaction(self._db):
            entity = self._repo.update(participant_id, **fields)
            participant_updated.send(self.__class__, participant=entity)
            return entity

    def delete(self, participant_id: int) -> None:
        with transaction(self._db):
            self._repo.delete(participant_id)
            participant_deleted.send(
                self.__class__, participant_id=participant_id
            )
