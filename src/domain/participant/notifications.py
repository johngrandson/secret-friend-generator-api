"""Participant notification handlers — pure business logic, no infrastructure deps."""
import logging

log = logging.getLogger(__name__)


def on_participant_joined(*, participant_id: int, group_id: int) -> None:
    """Handle participant-joined notification."""
    log.info(
        "notification: participant joined — id=%s group_id=%s",
        participant_id,
        group_id,
    )


def on_participant_deleted(*, participant_id: int) -> None:
    """Handle participant-deleted notification."""
    log.info("notification: participant deleted — id=%s", participant_id)
