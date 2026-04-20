"""Participant transactional handlers — errors propagate, rolling back the transaction.

These handlers have NO @isolated decorator. If they fail, the entire
transaction rolls back. Use for cross-domain state changes that
MUST succeed or the whole operation fails.
"""
from sqlalchemy.orm import Session

from src.domain.secret_friend.signals import secret_friend_assigned


def _reveal_participant_on_assignment(
    sender: type, *, participant_id: int, db_session: Session, **kwargs: object
) -> None:
    """Mark participant as REVEALED when their secret friend is assigned.

    Listens to: secret_friend.assigned (from secret_friend domain)
    """
    from src.domain.participant.schemas import ParticipantStatus, ParticipantUpdate
    from src.domain.participant.service import ParticipantService

    ParticipantService.update(
        participant_id=participant_id,
        payload=ParticipantUpdate(status=ParticipantStatus.REVEALED),
        db_session=db_session,
    )


def register_transactional() -> None:
    """Connect participant transactional handlers to their signals."""
    secret_friend_assigned.connect(_reveal_participant_on_assignment)
