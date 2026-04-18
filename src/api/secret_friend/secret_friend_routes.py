from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.domain.participant.participant_schemas import ParticipantStatus, ParticipantUpdate
from src.domain.participant.participant_service import ParticipantService
from src.domain.secret_friend.secret_friend_schemas import SecretFriendLink
from src.domain.secret_friend.secret_friend_service import SecretFriendService
from src.api.api_dependencies import get_db
from src.domain.shared.database_transaction import transaction
from src.domain.shared.domain_exceptions import ConflictError, NotFoundError

router = APIRouter()


@router.get("/{group_id}/{participant_id}")
def generate_secret_friends(
    group_id: int, participant_id: int, db_session: Session = Depends(get_db)
):
    try:
        with transaction(db_session):
            participant = ParticipantService.get_by_id(
                participant_id=participant_id, db_session=db_session
            )
            all_participants = ParticipantService.get_by_group_id(
                group_id=group_id, db_session=db_session
            )

            secret_friend_link = SecretFriendService.sort_secret_friends(
                participant=participant, participants=all_participants
            )

            ParticipantService.update(
                participant_id=participant_id,
                payload=ParticipantUpdate(status=ParticipantStatus.REVEALED),
                db_session=db_session,
            )
            SecretFriendService.link(
                secret_friend=SecretFriendLink(
                    gift_giver_id=participant_id,
                    gift_receiver_id=secret_friend_link.gift_receiver_id,
                ),
                db_session=db_session,
            )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"secret_friends": secret_friend_link}
