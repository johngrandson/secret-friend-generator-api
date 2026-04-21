from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.domain.secret_friend.schemas import SecretFriendRead
from src.domain.secret_friend.service import SecretFriendService
from src.api.dependencies import get_db

router = APIRouter()


@router.post("/{group_id}/{participant_id}")
def assign_secret_friend(
    group_id: int, participant_id: int, db_session: Session = Depends(get_db)
):
    result = SecretFriendService.assign(
        group_id=group_id, participant_id=participant_id, db_session=db_session
    )
    return {"secret_friends": result}


@router.get("/{secret_friend_id}", response_model=SecretFriendRead)
def get_secret_friend(secret_friend_id: int, db_session: Session = Depends(get_db)):
    return SecretFriendService.get_by_id(
        secret_friend_id=secret_friend_id, db_session=db_session
    )


@router.delete("/{secret_friend_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_secret_friend(secret_friend_id: int, db_session: Session = Depends(get_db)):
    SecretFriendService.delete(secret_friend_id=secret_friend_id, db_session=db_session)
