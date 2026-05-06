"""Participant use cases — depend on Protocols only, no infrastructure imports."""

from src.domain.participant.entities import Participant
from src.domain.participant.repositories import IParticipantRepository
from src.domain.participant.signals import (
    participant_created,
    participant_deleted,
    participant_updated,
)
from src.domain.participant.value_objects import ParticipantStatus
from src.domain.shared.unit_of_work import UnitOfWork


class ParticipantService:
    def __init__(
        self, repo: IParticipantRepository, uow: UnitOfWork
    ) -> None:
        self._repo = repo
        self._uow = uow

    def create(self, *, name: str, group_id: int) -> Participant:
        with self._uow.atomic():
            entity = self._repo.create(
                Participant(name=name, group_id=group_id)
            )
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
        with self._uow.atomic():
            entity = self._repo.update(
                participant_id,
                name=name,
                gift_hint=gift_hint,
                status=status,
            )
            participant_updated.send(self.__class__, participant=entity)
            return entity

    def delete(self, participant_id: int) -> None:
        with self._uow.atomic():
            self._repo.delete(participant_id)
            participant_deleted.send(
                self.__class__, participant_id=participant_id
            )
