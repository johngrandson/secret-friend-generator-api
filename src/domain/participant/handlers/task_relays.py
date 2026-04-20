"""Participant task relays — bridge lifecycle events to the background task queue."""

from src.domain.participant.schemas import ParticipantRead
from src.domain.participant.signals import participant_created, participant_deleted
from src.shared.signals import isolated
from src.shared.task_backend import dispatch_task


@isolated
def _relay_participant_created(
    sender: type, *, participant: ParticipantRead, **kwargs: object
) -> None:
    dispatch_task(
        "notifications.participant_joined",
        participant_id=participant.id,
        group_id=participant.group_id,
    )


@isolated
def _relay_participant_deleted(
    sender: type, *, participant_id: int, **kwargs: object
) -> None:
    dispatch_task("notifications.participant_deleted", participant_id=participant_id)


def register_task_relays() -> None:
    """Connect participant task relay handlers to their signals."""
    participant_created.connect(_relay_participant_created)
    participant_deleted.connect(_relay_participant_deleted)
