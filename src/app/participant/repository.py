from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..group.model import Group
from ..participant.model import Participant
from ..participant.schema import ParticipantCreate, ParticipantUpdate
from ..secret_friend.model import SecretFriend


class ParticipantRepository:
    @staticmethod
    def create_new_participant(participant: ParticipantCreate, db_session: Session):
        try:
            new_participant = Participant(**participant.model_dump(exclude_unset=True))
            group = db_session.get(Group, new_participant.group_id)
            if not group:
                raise ValueError("Group not found")

            db_session.add(new_participant)
            db_session.commit()
            db_session.refresh(new_participant)
        except IntegrityError as e:
            db_session.rollback()

            print(f"Integrity error during participant creation: {str(e)}")
            raise ValueError(
                "Participant creation failed. Ensure unique constraints are met."
            )
        return new_participant

    @staticmethod
    def get_all_participants(*, db_session: Session):
        try:
            participants = (
                db_session.query(Participant)
                .options(
                    joinedload(Participant.gift_giver).joinedload(SecretFriend.receiver)
                )
                .all()
            )
        except IntegrityError as e:
            print(f"Integrity error during participant creation: {str(e)}")
            raise ValueError(
                "Participant creation failed. Ensure unique constraints are met."
            )
        return participants

    @staticmethod
    def get_participant_by_id(id: int, db_session: Session):
        try:
            participant = (
                db_session.query(Participant)
                .options(
                    joinedload(Participant.gift_giver).joinedload(SecretFriend.receiver)
                )
                .filter(Participant.id == id)
                .one_or_none()
            )
            if not participant:
                raise ValueError("Participant not found")
        except IntegrityError as e:
            print(f"Integrity error during participant creation: {str(e)}")
            raise ValueError(
                "Participant creation failed. Ensure unique constraints are met."
            )
        return participant

    @staticmethod
    def update_participant(
        id: int, participant_payload: ParticipantUpdate, db_session: Session
    ):
        try:
            existing_participant = db_session.get(Participant, id)
            if not existing_participant:
                raise ValueError("Participant not found")

            update_data = participant_payload.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(existing_participant, key, value)

            existing_participant.updated_at = datetime.now()

            db_session.commit()
            db_session.refresh(existing_participant)
        except IntegrityError as e:
            db_session.rollback()

            print(f"Integrity error during participant update: {str(e)}")
            raise ValueError(
                "Participant update failed. Ensure unique constraints are met."
            )
        return existing_participant
