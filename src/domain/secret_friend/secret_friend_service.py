import random

from sqlalchemy.orm import Session

from src.domain.participant.participant_schemas import ParticipantRead
from src.domain.secret_friend.secret_friend_repository import SecretFriendRepository
from src.domain.secret_friend.secret_friend_schemas import SecretFriendLink, SecretFriendRead


class SecretFriendService:
    @staticmethod
    def sort_secret_friends(
        participant: ParticipantRead, participants: list[ParticipantRead]
    ) -> SecretFriendLink:
        """Shuffles participants and assigns a secret friend avoiding self-linking."""
        if len(participants) < 2:
            raise ValueError("At least 2 participants are required to assign secret friends.")
        random.shuffle(participants)

        for receiver in participants[1:] + [participants[0]]:
            if receiver.id == participant.id:
                continue
            return SecretFriendLink(
                gift_giver_id=participant.id, gift_receiver_id=receiver.id
            )
        raise ValueError("Unable to assign a secret friend for the participant.")

    @staticmethod
    def link(secret_friend: SecretFriendLink, db_session: Session) -> SecretFriendRead:
        result = SecretFriendRepository.link(
            secret_friend=secret_friend, db_session=db_session
        )
        return SecretFriendRead.model_validate(result)
