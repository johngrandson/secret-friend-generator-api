from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_participant_service
from src.api.participant.schemas import (
    ParticipantCreate,
    ParticipantList,
    ParticipantRead,
    ParticipantUpdate,
)
from src.domain.participant.service import ParticipantService

router = APIRouter()


@router.post(
    "", response_model=ParticipantRead, status_code=status.HTTP_201_CREATED
)
def create_participant(
    participant: ParticipantCreate,
    service: ParticipantService = Depends(get_participant_service),
) -> ParticipantRead:
    entity = service.create(
        name=participant.name, group_id=participant.group_id
    )
    return ParticipantRead.model_validate(entity)


@router.get("", response_model=ParticipantList)
def list_participants(
    service: ParticipantService = Depends(get_participant_service),
) -> ParticipantList:
    entities = service.get_all()
    return ParticipantList(
        participants=[ParticipantRead.model_validate(p) for p in entities]
    )


@router.get("/{participant_id}", response_model=ParticipantRead)
def get_participant(
    participant_id: int,
    service: ParticipantService = Depends(get_participant_service),
) -> ParticipantRead:
    return ParticipantRead.model_validate(service.get_by_id(participant_id))


@router.patch("/{participant_id}", response_model=ParticipantRead)
def update_participant(
    participant_id: int,
    payload: ParticipantUpdate,
    service: ParticipantService = Depends(get_participant_service),
) -> ParticipantRead:
    entity = service.update(
        participant_id,
        name=payload.name,
        gift_hint=payload.gift_hint,
        status=payload.status,
    )
    return ParticipantRead.model_validate(entity)


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    participant_id: int,
    service: ParticipantService = Depends(get_participant_service),
) -> None:
    service.delete(participant_id)
