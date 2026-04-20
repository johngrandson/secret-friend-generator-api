from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.domain.group.model import Group
from src.domain.participant.model import Participant
from src.domain.participant.schemas import ParticipantCreate, ParticipantUpdate
from src.domain.secret_friend.model import SecretFriend
from src.shared.exceptions import ConflictError, NotFoundError


class ParticipantRepository:
    @staticmethod
    def create(participant: ParticipantCreate, db_session: Session) -> Participant:
        group = db_session.get(Group, participant.group_id)
        if not group:
            raise NotFoundError("Group not found")

        new_participant = Participant(**participant.model_dump())
        try:
            db_session.add(new_participant)
            db_session.flush()
            db_session.refresh(new_participant)
        except IntegrityError:
            raise ConflictError("Participant creation failed. Unique constraint violated.")
        return new_participant

    @staticmethod
    def get_all(db_session: Session) -> list[Participant]:
        stmt = (
            select(Participant)
            .options(joinedload(Participant.gift_giver).joinedload(SecretFriend.receiver))
        )
        return list(db_session.execute(stmt).scalars().unique().all())

    @staticmethod
    def get_by_group_id(group_id: int, db_session: Session) -> list[Participant]:
        stmt = (
            select(Participant)
            .where(Participant.group_id == group_id)
            .options(joinedload(Participant.gift_giver).joinedload(SecretFriend.receiver))
        )
        return list(db_session.execute(stmt).scalars().unique().all())

    @staticmethod
    def get_by_id(participant_id: int, db_session: Session) -> Participant:
        stmt = (
            select(Participant)
            .options(joinedload(Participant.gift_giver).joinedload(SecretFriend.receiver))
            .where(Participant.id == participant_id)
        )
        participant = db_session.execute(stmt).scalars().unique().one_or_none()
        if not participant:
            raise NotFoundError("Participant not found")
        return participant

    @staticmethod
    def update(
        participant_id: int, payload: ParticipantUpdate, db_session: Session
    ) -> Participant:
        participant = db_session.get(Participant, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(participant, key, value)

        try:
            db_session.flush()
            db_session.refresh(participant)
        except IntegrityError:
            raise ConflictError("Participant update failed. Unique constraint violated.")
        return participant
