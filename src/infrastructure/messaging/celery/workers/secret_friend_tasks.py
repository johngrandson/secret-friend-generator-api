"""Celery task wrappers for secret friend notifications."""
from celery import shared_task

from src.domain.secret_friend.notifications import (
    on_secret_friend_assigned,
    on_secret_friend_deleted,
)


@shared_task(name="notifications.secret_friend_assigned")
def secret_friend_assigned(*, assignment_id: int, group_id: int) -> None:
    on_secret_friend_assigned(assignment_id=assignment_id, group_id=group_id)


@shared_task(name="notifications.secret_friend_deleted")
def secret_friend_deleted(*, secret_friend_id: int) -> None:
    on_secret_friend_deleted(secret_friend_id=secret_friend_id)
