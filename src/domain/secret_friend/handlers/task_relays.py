"""Secret friend task relays — bridge lifecycle events to the background task queue."""

from src.domain.secret_friend.entities import SecretFriend
from src.domain.secret_friend.signals import (
    secret_friend_assigned,
    secret_friend_deleted,
)
from src.shared.signals import isolated
from src.shared.task_backend import dispatch_task


@isolated
def _relay_secret_friend_assigned(
    sender: type,
    *,
    assignment: SecretFriend,
    group_id: int,
    **kwargs: object,
) -> None:
    dispatch_task(
        "notifications.secret_friend_assigned",
        assignment_id=assignment.id,
        group_id=group_id,
    )


@isolated
def _relay_secret_friend_deleted(
    sender: type, *, secret_friend_id: int, **kwargs: object
) -> None:
    dispatch_task(
        "notifications.secret_friend_deleted",
        secret_friend_id=secret_friend_id,
    )


def register_task_relays() -> None:
    """Connect secret friend task relay handlers to their signals."""
    secret_friend_assigned.connect(_relay_secret_friend_assigned)
    secret_friend_deleted.connect(_relay_secret_friend_deleted)
