"""SecretFriend use cases — orchestrate participant lookup + assignment."""

import random

from sqlalchemy.orm import Session

from src.domain.participant.entities import Participant
from src.domain.participant.service import ParticipantService
from src.domain.secret_friend.entities import SecretFriend
from src.domain.secret_friend.repositories import ISecretFriendRepository
from src.domain.secret_friend.signals import (
    secret_friend_assigned,
    secret_friend_deleted,
)
from src.infrastructure.persistence import transaction
from src.shared.exceptions import BusinessRuleError


class SecretFriendService:
    def __init__(
        self,
        repo: ISecretFriendRepository,
        participant_service: ParticipantService,
        db: Session,
    ) -> None:
        self._repo = repo
        self._participants = participant_service
        self._db = db

    def assign(self, group_id: int, participant_id: int) -> SecretFriend:
        with transaction(self._db):
            participant = self._participants.get_by_id(participant_id)
            all_participants = self._participants.get_by_group_id(group_id)
            link = self._sort_secret_friends(participant, all_participants)
            entity = self._repo.link(link)
            secret_friend_assigned.send(
                self.__class__,
                assignment=entity,
                group_id=group_id,
                participant_id=participant_id,
                db_session=self._db,
            )
            return entity

    @staticmethod
    def _sort_secret_friends(
        participant: Participant, participants: list[Participant]
    ) -> SecretFriend:
        if len(participants) < 2:
            raise BusinessRuleError(
                "At least 2 participants are required to assign secret friends."
            )
        random.shuffle(participants)
        for receiver in participants[1:] + [participants[0]]:
            if receiver.id == participant.id:
                continue
            if participant.id is None or receiver.id is None:
                continue
            return SecretFriend(
                gift_giver_id=participant.id, gift_receiver_id=receiver.id
            )
        raise BusinessRuleError(
            "Unable to assign a secret friend for the participant."
        )

    def link(
        self, *, gift_giver_id: int, gift_receiver_id: int
    ) -> SecretFriend:
        return self._repo.link(
            SecretFriend(
                gift_giver_id=gift_giver_id,
                gift_receiver_id=gift_receiver_id,
            )
        )

    def get_by_id(self, secret_friend_id: int) -> SecretFriend:
        return self._repo.get_by_id(secret_friend_id)

    def delete(self, secret_friend_id: int) -> None:
        with transaction(self._db):
            self._repo.delete(secret_friend_id)
            secret_friend_deleted.send(
                self.__class__, secret_friend_id=secret_friend_id
            )
