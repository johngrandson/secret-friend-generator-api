from sqlalchemy.orm import Session

from src.domain.participant.repository import ParticipantRepository
from src.domain.participant.schemas import (
    ParticipantCreate,
    ParticipantList,
    ParticipantRead,
    ParticipantUpdate,
)


class ParticipantService:
    @staticmethod
    def create(participant: ParticipantCreate, db_session: Session) -> ParticipantRead:
        result = ParticipantRepository.create(participant=participant, db_session=db_session)
        return ParticipantRead.model_validate(result)

    @staticmethod
    def get_all(db_session: Session) -> ParticipantList:
        participants = ParticipantRepository.get_all(db_session=db_session)
        items = [ParticipantRead.model_validate(p) for p in participants]
        return ParticipantList(participants=items)

    @staticmethod
    def get_by_group_id(group_id: int, db_session: Session) -> list[ParticipantRead]:
        participants = ParticipantRepository.get_by_group_id(
            group_id=group_id, db_session=db_session
        )
        return [ParticipantRead.model_validate(p) for p in participants]

    @staticmethod
    def get_by_id(participant_id: int, db_session: Session) -> ParticipantRead:
        result = ParticipantRepository.get_by_id(
            participant_id=participant_id, db_session=db_session
        )
        return ParticipantRead.model_validate(result)

    @staticmethod
    def update(
        participant_id: int, payload: ParticipantUpdate, db_session: Session
    ) -> ParticipantRead:
        result = ParticipantRepository.update(
            participant_id=participant_id, payload=payload, db_session=db_session
        )
        return ParticipantRead.model_validate(result)
