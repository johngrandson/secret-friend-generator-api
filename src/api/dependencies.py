"""FastAPI DI factories — wire driven adapters into use cases per request."""

from fastapi import Depends
from sqlalchemy.orm import Session

from src.domain.group.service import GroupService
from src.domain.participant.service import ParticipantService
from src.domain.secret_friend.service import SecretFriendService
from src.infrastructure.persistence import get_db
from src.infrastructure.repositories.group_repository import (
    PostgresGroupRepository,
)
from src.infrastructure.repositories.participant_repository import (
    PostgresParticipantRepository,
)
from src.infrastructure.repositories.secret_friend_repository import (
    PostgresSecretFriendRepository,
)


def get_group_service(db: Session = Depends(get_db)) -> GroupService:
    return GroupService(repo=PostgresGroupRepository(db), db=db)


def get_participant_service(
    db: Session = Depends(get_db),
) -> ParticipantService:
    return ParticipantService(repo=PostgresParticipantRepository(db), db=db)


def get_secret_friend_service(
    db: Session = Depends(get_db),
    participant_service: ParticipantService = Depends(get_participant_service),
) -> SecretFriendService:
    return SecretFriendService(
        repo=PostgresSecretFriendRepository(db),
        participant_service=participant_service,
        db=db,
    )


__all__ = [
    "get_db",
    "get_group_service",
    "get_participant_service",
    "get_secret_friend_service",
]
