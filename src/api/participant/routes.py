from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.domain.participant.schemas import (
    ParticipantCreate,
    ParticipantList,
    ParticipantRead,
    ParticipantUpdate,
)
from src.domain.participant.service import ParticipantService
from src.api.dependencies import get_db

router = APIRouter()


@router.post("", response_model=ParticipantRead, status_code=status.HTTP_201_CREATED)
def create_participant(
    participant: ParticipantCreate, db_session: Session = Depends(get_db)
):
    return ParticipantService.create(participant=participant, db_session=db_session)


@router.get("", response_model=ParticipantList)
def list_participants(db_session: Session = Depends(get_db)):
    return ParticipantService.get_all(db_session=db_session)


@router.get("/{participant_id}", response_model=ParticipantRead)
def get_participant(participant_id: int, db_session: Session = Depends(get_db)):
    return ParticipantService.get_by_id(
        participant_id=participant_id, db_session=db_session
    )


@router.patch("/{participant_id}", response_model=ParticipantRead)
def update_participant(
    participant_id: int,
    payload: ParticipantUpdate,
    db_session: Session = Depends(get_db),
):
    return ParticipantService.update(
        participant_id=participant_id, payload=payload, db_session=db_session
    )


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(participant_id: int, db_session: Session = Depends(get_db)):
    ParticipantService.delete(participant_id=participant_id, db_session=db_session)
