"""Celery task wrappers for group notifications."""
from celery import shared_task

from src.domain.group.notifications import (
    on_group_created,
    on_group_deleted,
    on_group_updated,
)


@shared_task(name="notifications.group_created")
def group_created(*, group_id: int, group_name: str) -> None:
    on_group_created(group_id=group_id, group_name=group_name)


@shared_task(name="notifications.group_updated")
def group_updated(*, group_id: int, group_name: str) -> None:
    on_group_updated(group_id=group_id, group_name=group_name)


@shared_task(name="notifications.group_deleted")
def group_deleted(*, group_id: int) -> None:
    on_group_deleted(group_id=group_id)
