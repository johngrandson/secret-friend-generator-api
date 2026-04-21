"""Celery task wrappers for participant notifications."""
from celery import shared_task

from src.domain.participant.notifications import (
    on_participant_deleted,
    on_participant_joined,
)


@shared_task(name="notifications.participant_joined")
def participant_joined(*, participant_id: int, group_id: int) -> None:
    on_participant_joined(participant_id=participant_id, group_id=group_id)


@shared_task(name="notifications.participant_deleted")
def participant_deleted(*, participant_id: int) -> None:
    on_participant_deleted(participant_id=participant_id)
