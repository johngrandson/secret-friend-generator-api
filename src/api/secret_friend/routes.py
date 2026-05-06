from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_secret_friend_service
from src.api.secret_friend.schemas import SecretFriendRead
from src.domain.secret_friend.service import SecretFriendService

router = APIRouter()


@router.post("/{group_id}/{participant_id}")
def assign_secret_friend(
    group_id: int,
    participant_id: int,
    service: SecretFriendService = Depends(get_secret_friend_service),
) -> dict[str, SecretFriendRead]:
    entity = service.assign(group_id=group_id, participant_id=participant_id)
    return {"secret_friends": SecretFriendRead.model_validate(entity)}


@router.get("/{secret_friend_id}", response_model=SecretFriendRead)
def get_secret_friend(
    secret_friend_id: int,
    service: SecretFriendService = Depends(get_secret_friend_service),
) -> SecretFriendRead:
    return SecretFriendRead.model_validate(service.get_by_id(secret_friend_id))


@router.delete(
    "/{secret_friend_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_secret_friend(
    secret_friend_id: int,
    service: SecretFriendService = Depends(get_secret_friend_service),
) -> None:
    service.delete(secret_friend_id)
