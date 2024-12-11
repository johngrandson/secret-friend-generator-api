from sqlalchemy.orm import Session

from ..participant.schema import (
    ParticipantCreate,
    ParticipantRead,
    ParticipantUpdate,
    ParticipantsRead,
)
from ..participant.repository import ParticipantRepository


class ParticipantService:
    @staticmethod
    def create(participant: ParticipantCreate, db_session: Session) -> ParticipantRead:
        """Business logic for creating a new participant"""
        participant = ParticipantRepository.create_new_participant(
            participant=participant, db_session=db_session
        )
        return ParticipantRead.model_validate(participant)

    @staticmethod
    def get_all(db_session: Session) -> ParticipantsRead:
        """Business logic for getting all participants"""
        participants = ParticipantRepository.get_all_participants(db_session=db_session)
        return ParticipantsRead.model_validate(participants)

    @staticmethod
    def get_by_id(id: str, db_session: Session) -> ParticipantRead:
        """Business logic for getting a participant by id"""
        participant = ParticipantRepository.get_participant_by_id(
            id, db_session=db_session
        )
        return ParticipantRead.model_validate(participant)

    @staticmethod
    def update(
        id: str, participant_payload: ParticipantUpdate, db_session: Session
    ) -> ParticipantRead:
        """Business logic for updating a participant"""
        participant = ParticipantRepository.update_participant(
            id=id, participant_payload=participant_payload, db_session=db_session
        )
        return ParticipantRead.model_validate(participant)
