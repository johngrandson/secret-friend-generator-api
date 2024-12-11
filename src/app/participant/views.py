from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Depends

from ..database.session import get_db
from ..participant.schema import ParticipantCreate, ParticipantRead, ParticipantUpdate
from ..participant.service import ParticipantService


router = APIRouter(
    tags=["participants"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "",
    response_model=ParticipantRead,
    status_code=status.HTTP_201_CREATED,
)
def create_participant(
    participant: ParticipantCreate, db_session: Session = Depends(get_db)
):
    try:
        participant = ParticipantService.create(
            participant=participant, db_session=db_session
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    return participant


@router.get("/{participant_id}")
def get_participant_controller(
    participant_id: int, db_session: Session = Depends(get_db)
):
    try:
        participant = ParticipantService.get_by_id(
            id=participant_id, db_session=db_session
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    return participant


@router.patch("/{participant_id}")
def update_participant_controller(
    participant_id: int,
    participant_update: ParticipantUpdate,
    db_session: Session = Depends(get_db),
):
    try:
        updated_participant = ParticipantService.update(
            id=participant_id, participant=participant_update, db_session=db_session
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    return updated_participant
