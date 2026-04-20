"""Participant lifecycle handlers.

Two categories of handlers:
- @isolated: Side-effects (logging, notifications) — errors are swallowed.
- No decorator: Transactional handlers — errors propagate so the
  transaction rolls back. Use for cross-domain state changes that
  MUST succeed or the whole operation fails.
"""
import logging
from typing import Any

from sqlalchemy.orm import Session

from src.domain.participant.signals import participant_created, participant_updated
from src.domain.secret_friend.signals import secret_friend_assigned
from src.domain.shared.signals import isolated
from src.domain.shared.task_backend import dispatch_task

log = logging.getLogger(__name__)


# ── Side-effect handlers (@isolated) ─────────────────────────────────────────

@isolated
def _on_participant_created(sender: type, *, participant: Any, **_: Any) -> None:
    log.info(
        "lifecycle: participant created — id=%s group_id=%s",
        participant.id,
        participant.group_id,
    )


@isolated
def _on_participant_updated(sender: type, *, participant: Any, **_: Any) -> None:
    log.info(
        "lifecycle: participant updated — id=%s status=%s",
        participant.id,
        participant.status,
    )


# ── Transactional handlers (no @isolated — errors roll back) ────────────────

def _reveal_participant_on_assignment(
    sender: type, *, participant_id: int, db_session: Session, **_: Any
) -> None:
    """Mark participant as REVEALED when their secret friend is assigned.

    This is a transactional handler: if it fails, the entire assignment
    transaction rolls back. This ensures data consistency — an assignment
    cannot exist without the participant being REVEALED.

    Listens to: secret_friend.assigned (from secret_friend domain)
    """
    from src.domain.participant.schemas import ParticipantStatus, ParticipantUpdate
    from src.domain.participant.service import ParticipantService

    ParticipantService.update(
        participant_id=participant_id,
        payload=ParticipantUpdate(status=ParticipantStatus.REVEALED),
        db_session=db_session,
    )


# ── Task relays (bridge to background task queue) ────────────────────────────

@isolated
def _relay_participant_created(sender: type, *, participant: Any, **_: Any) -> None:
    dispatch_task(
        "notifications.participant_joined",
        participant_id=participant.id,
        group_id=participant.group_id,
    )


# ── Registration ─────────────────────────────────────────────────────────────

def register() -> None:
    """Connect participant lifecycle handlers to their signals."""
    # Own signals
    participant_created.connect(_on_participant_created)
    participant_updated.connect(_on_participant_updated)
    participant_created.connect(_relay_participant_created)
    # Cross-domain: react to secret_friend assignment
    secret_friend_assigned.connect(_reveal_participant_on_assignment)
