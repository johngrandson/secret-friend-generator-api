"""Postgres adapter for IParticipantRepository — maps ORM ↔ Participant entity."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.domain.participant.entities import Participant
from src.domain.participant.value_objects import ParticipantStatus
from src.infrastructure.persistence.models import (
    GroupORM,
    ParticipantORM,
    SecretFriendORM,
)
from src.shared.exceptions import ConflictError, NotFoundError


def _to_entity(orm: ParticipantORM) -> Participant:
    return Participant(
        id=orm.id,
        name=orm.name,
        group_id=orm.group_id,
        gift_hint=orm.gift_hint,
        status=orm.status,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


class PostgresParticipantRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, participant: Participant) -> Participant:
        if self._db.get(GroupORM, participant.group_id) is None:
            raise NotFoundError("Group not found")
        orm = ParticipantORM(
            name=participant.name,
            group_id=participant.group_id,
            gift_hint=participant.gift_hint,
            status=participant.status,
        )
        try:
            self._db.add(orm)
            self._db.flush()
            self._db.refresh(orm)
        except IntegrityError as exc:
            raise ConflictError(
                "Participant creation failed. Unique constraint violated."
            ) from exc
        return _to_entity(orm)

    def get_all(self) -> list[Participant]:
        stmt = select(ParticipantORM).options(
            joinedload(ParticipantORM.gift_giver).joinedload(
                SecretFriendORM.receiver
            )
        )
        rows = self._db.execute(stmt).scalars().unique().all()
        return [_to_entity(p) for p in rows]

    def get_by_group_id(self, group_id: int) -> list[Participant]:
        stmt = (
            select(ParticipantORM)
            .where(ParticipantORM.group_id == group_id)
            .options(
                joinedload(ParticipantORM.gift_giver).joinedload(
                    SecretFriendORM.receiver
                )
            )
        )
        rows = self._db.execute(stmt).scalars().unique().all()
        return [_to_entity(p) for p in rows]

    def get_by_id(self, participant_id: int) -> Participant:
        stmt = (
            select(ParticipantORM)
            .options(
                joinedload(ParticipantORM.gift_giver).joinedload(
                    SecretFriendORM.receiver
                )
            )
            .where(ParticipantORM.id == participant_id)
        )
        orm = self._db.execute(stmt).scalars().unique().one_or_none()
        if orm is None:
            raise NotFoundError("Participant not found")
        return _to_entity(orm)

    def update(
        self,
        participant_id: int,
        *,
        name: str | None = None,
        gift_hint: str | None = None,
        status: ParticipantStatus | None = None,
    ) -> Participant:
        orm = self._db.get(ParticipantORM, participant_id)
        if orm is None:
            raise NotFoundError("Participant not found")
        if name is not None:
            orm.name = name
        if gift_hint is not None:
            orm.gift_hint = gift_hint
        if status is not None:
            orm.status = status
        try:
            self._db.flush()
            self._db.refresh(orm)
        except IntegrityError as exc:
            raise ConflictError(
                "Participant update failed. Unique constraint violated."
            ) from exc
        return _to_entity(orm)

    def delete(self, participant_id: int) -> None:
        orm = self._db.get(ParticipantORM, participant_id)
        if orm is None:
            raise NotFoundError("Participant not found")
        self._db.delete(orm)
        self._db.flush()
