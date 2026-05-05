"""Participant transactional handler — cross-domain reaction to assignment.

Errors propagate, rolling back the transaction.
"""

from sqlalchemy.orm import Session

from src.domain.secret_friend.signals import secret_friend_assigned


def _reveal_participant_on_assignment(
    sender: type,
    *,
    participant_id: int,
    db_session: Session,
    **kwargs: object,
) -> None:
    """Mark participant as REVEALED when their secret friend is assigned."""
    from src.domain.participant.service import ParticipantService
    from src.domain.participant.value_objects import ParticipantStatus
    from src.infrastructure.repositories.participant_repository import (
        PostgresParticipantRepository,
    )

    repo = PostgresParticipantRepository(db_session)
    service = ParticipantService(repo=repo, db=db_session)
    service.update(participant_id, status=ParticipantStatus.REVEALED)


def register_transactional() -> None:
    """Connect participant transactional handlers to their signals."""
    secret_friend_assigned.connect(_reveal_participant_on_assignment)
