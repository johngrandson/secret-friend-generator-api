import random

from sqlalchemy.orm import Session
from typing import List

from ..participant.schema import ParticipantRead
from ..secret_friend.repository import LinkSecretFriendRepository
from ..secret_friend.schema import LinkSecretFriend


class SecretFriendService:
    @staticmethod
    def sort_secret_friends(
        participant: ParticipantRead, participants: List[ParticipantRead]
    ) -> LinkSecretFriend:
        """
        Sorts participants into secret friends by shuffling and avoiding self-linking.
        """
        random.shuffle(participants)

        for receiver in participants[1:] + [participants[0]]:
            if receiver.id == participant.id:
                continue

            return LinkSecretFriend(
                gift_giver_id=participant.id, gift_receiver_id=receiver.id
            )
        raise ValueError("Unable to assign a secret friend for the participant.")


    @staticmethod
    def link_secret_friend(*, secret_friend: LinkSecretFriend, db_session: Session):
        """
        Persists a secret friend link in the database.
        """
        return LinkSecretFriendRepository.link_secret_friend(
            secret_friend=secret_friend, db_session=db_session
        )
