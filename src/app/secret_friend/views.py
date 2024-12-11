from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from ..database.session import get_db
from ..group.model import Group
from ..group.service import GroupService
from ..participant.model import Participant, StatusEnum
from ..participant.schema import ParticipantUpdate
from ..participant.service import ParticipantService
from ..secret_friend.schema import LinkSecretFriend
from ..secret_friend.service import SecretFriendService


router = APIRouter(
    tags=["secret-friends"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@router.get("/{group_id}/{participant_id}")
def generate_secret_friends(
    group_id: str, participant_id: str, db_session: Session = Depends(get_db)
):
    """Generate secret friends"""
    try:
        group: Group = GroupService.get_by_id(id=group_id, db_session=db_session)
        participant: Participant = ParticipantService.get_by_id(
            id=participant_id, db_session=db_session
        )
        secret_friends: LinkSecretFriend = SecretFriendService.sort_secret_friends(
            participant=participant, participants=group.participants
        )

        ParticipantService.update(
            id=participant_id,
            participant_payload=ParticipantUpdate(status=StatusEnum.REVEALED),
            db_session=db_session,
        )

        SecretFriendService.link_secret_friend(
            secret_friend=LinkSecretFriend(
                gift_giver_id=participant_id,
                gift_receiver_id=secret_friends.gift_receiver_id,
            ),
            db_session=db_session,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e) or "An unexpected error occurred")

    return {"secret_friends": secret_friends}
