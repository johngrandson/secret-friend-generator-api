"""Group task relays — bridge lifecycle events to the background task queue."""

from src.domain.group.entities import Group
from src.domain.group.signals import group_created, group_deleted, group_updated
from src.shared.signals import isolated
from src.shared.task_backend import dispatch_task


@isolated
def _relay_group_created(
    sender: type, *, group: Group, **kwargs: object
) -> None:
    dispatch_task(
        "notifications.group_created", group_id=group.id, group_name=group.name
    )


@isolated
def _relay_group_updated(
    sender: type, *, group: Group, **kwargs: object
) -> None:
    dispatch_task(
        "notifications.group_updated", group_id=group.id, group_name=group.name
    )


@isolated
def _relay_group_deleted(
    sender: type, *, group_id: int, **kwargs: object
) -> None:
    dispatch_task("notifications.group_deleted", group_id=group_id)


def register_task_relays() -> None:
    """Connect group task relay handlers to their signals."""
    group_created.connect(_relay_group_created)
    group_updated.connect(_relay_group_updated)
    group_deleted.connect(_relay_group_deleted)
