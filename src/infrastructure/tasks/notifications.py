"""Notification task definitions — executed by the Celery worker.

Task names match the strings used in domain handler task_relays.
The FastAPI process dispatches these via send_task() and never imports this module.
"""
import logging

from celery import shared_task

log = logging.getLogger(__name__)


# ── Group notifications ──────────────────────────────────────────────────────

@shared_task(name="notifications.group_created")
def group_created(*, group_id: int, group_name: str) -> None:
    log.info("notification: group created — id=%s name=%s", group_id, group_name)


@shared_task(name="notifications.group_updated")
def group_updated(*, group_id: int, group_name: str) -> None:
    log.info("notification: group updated — id=%s name=%s", group_id, group_name)


@shared_task(name="notifications.group_deleted")
def group_deleted(*, group_id: int) -> None:
    log.info("notification: group deleted — id=%s", group_id)


# ── Participant notifications ────────────────────────────────────────────────

@shared_task(name="notifications.participant_joined")
def participant_joined(*, participant_id: int, group_id: int) -> None:
    log.info("notification: participant joined — id=%s group_id=%s", participant_id, group_id)


@shared_task(name="notifications.participant_deleted")
def participant_deleted(*, participant_id: int) -> None:
    log.info("notification: participant deleted — id=%s", participant_id)


# ── Secret friend notifications ──────────────────────────────────────────────

@shared_task(name="notifications.secret_friend_assigned")
def secret_friend_assigned(*, assignment_id: int, group_id: int) -> None:
    log.info("notification: secret friend assigned — id=%s group_id=%s", assignment_id, group_id)


@shared_task(name="notifications.secret_friend_deleted")
def secret_friend_deleted(*, secret_friend_id: int) -> None:
    log.info("notification: secret friend deleted — id=%s", secret_friend_id)
