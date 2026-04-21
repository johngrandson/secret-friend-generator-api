"""Participant side-effect handlers — @isolated, errors are swallowed."""

import logging

from src.domain.participant.schemas import ParticipantRead
from src.domain.participant.signals import (
    participant_created,
    participant_deleted,
    participant_updated,
)
from src.shared.signals import isolated

log = logging.getLogger(__name__)


@isolated
def _on_participant_created(
    sender: type, *, participant: ParticipantRead, **kwargs: object
) -> None:
    log.info(
        "lifecycle: participant created — id=%s group_id=%s",
        participant.id,
        participant.group_id,
    )


@isolated
def _on_participant_updated(
    sender: type, *, participant: ParticipantRead, **kwargs: object
) -> None:
    log.info(
        "lifecycle: participant updated — id=%s status=%s",
        participant.id,
        participant.status,
    )


@isolated
def _on_participant_deleted(
    sender: type, *, participant_id: int, **kwargs: object
) -> None:
    log.info("lifecycle: participant deleted — id=%s", participant_id)


def register_side_effects() -> None:
    """Connect participant side-effect handlers to their signals."""
    participant_created.connect(_on_participant_created)
    participant_updated.connect(_on_participant_updated)
    participant_deleted.connect(_on_participant_deleted)
