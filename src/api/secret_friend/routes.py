from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
