import random

from sqlalchemy.orm import Session

from src.domain.participant.schemas import ParticipantRead
from src.domain.participant.service import ParticipantService
from src.domain.secret_friend.repository import SecretFriendRepository
from src.domain.secret_friend.schemas import SecretFriendLink, SecretFriendRead
from src.domain.secret_friend.signals import secret_friend_assigned
from src.domain.shared.database_transaction import transaction
from src.domain.shared.exceptions import BusinessRuleError


class SecretFriendService:
    @staticmethod
    def assign(
        group_id: int, participant_id: int, db_session: Session
    ) -> SecretFriendRead:
        """Orchestrates the full secret friend assignment flow.

        1. Fetch participant and group members
        2. Sort a secret friend (random, no self-link)
        3. Persist the link
        4. Emit signal (participant status update handled by participant handler)
        """
        with transaction(db_session):
            participant = ParticipantService.get_by_id(
                participant_id=participant_id, db_session=db_session
            )
            all_participants = ParticipantService.get_by_group_id(
                group_id=group_id, db_session=db_session
            )

            link = SecretFriendService.sort_secret_friends(participant, all_participants)

            result = SecretFriendRepository.link(
                secret_friend=SecretFriendLink(
                    gift_giver_id=participant_id,
                    gift_receiver_id=link.gift_receiver_id,
                ),
                db_session=db_session,
            )
            validated = SecretFriendRead.model_validate(result)
            secret_friend_assigned.send(
                SecretFriendService,
                assignment=validated,
                group_id=group_id,
                participant_id=participant_id,
                db_session=db_session,
            )
            return validated

    @staticmethod
    def sort_secret_friends(
        participant: ParticipantRead, participants: list[ParticipantRead]
    ) -> SecretFriendLink:
        """Shuffles participants and assigns a secret friend avoiding self-linking."""
        if len(participants) < 2:
            raise BusinessRuleError("At least 2 participants are required to assign secret friends.")
        random.shuffle(participants)

        for receiver in participants[1:] + [participants[0]]:
            if receiver.id == participant.id:
                continue
            return SecretFriendLink(
                gift_giver_id=participant.id, gift_receiver_id=receiver.id
            )
        raise BusinessRuleError("Unable to assign a secret friend for the participant.")

    @staticmethod
    def link(secret_friend: SecretFriendLink, db_session: Session) -> SecretFriendRead:
        result = SecretFriendRepository.link(
            secret_friend=secret_friend, db_session=db_session
        )
        return SecretFriendRead.model_validate(result)
