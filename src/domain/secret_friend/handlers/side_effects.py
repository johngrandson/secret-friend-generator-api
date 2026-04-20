"""Secret friend side-effect handlers — @isolated, errors are swallowed."""

import logging

from src.domain.secret_friend.schemas import SecretFriendRead
from src.domain.secret_friend.signals import (
    secret_friend_assigned,
    secret_friend_deleted,
)
from src.shared.signals import isolated

log = logging.getLogger(__name__)


@isolated
def _on_secret_friend_assigned(
    sender: type, *, assignment: SecretFriendRead, group_id: int, **kwargs: object
) -> None:
    log.info(
        "lifecycle: secret friend assigned — id=%s group_id=%s",
        assignment.id,
        group_id,
    )


@isolated
def _on_secret_friend_deleted(
    sender: type, *, secret_friend_id: int, **kwargs: object
) -> None:
    log.info("lifecycle: secret friend deleted — id=%s", secret_friend_id)


def register_side_effects() -> None:
    """Connect secret friend side-effect handlers to their signals."""
    secret_friend_assigned.connect(_on_secret_friend_assigned)
    secret_friend_deleted.connect(_on_secret_friend_deleted)
