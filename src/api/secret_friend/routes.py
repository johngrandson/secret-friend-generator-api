from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.domain.secret_friend.service import SecretFriendService
from src.api.dependencies import get_db
from src.domain.shared.database_transaction import transaction
from src.domain.shared.exceptions import ConflictError, NotFoundError

router = APIRouter()


@router.get("/{group_id}/{participant_id}")
def generate_secret_friends(
    group_id: int, participant_id: int, db_session: Session = Depends(get_db)
):
    try:
        with transaction(db_session):
            result = SecretFriendService.assign(
                group_id=group_id,
                participant_id=participant_id,
                db_session=db_session,
            )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"secret_friends": result}
