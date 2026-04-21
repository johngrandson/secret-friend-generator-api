"""Tests for secret_friend domain handlers (side-effects and task relays)."""

import logging
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from src.domain.group.schemas import GroupCreate
from src.domain.group.service import GroupService
from src.domain.participant.schemas import ParticipantCreate
from src.domain.participant.service import ParticipantService
from src.domain.secret_friend.repository import SecretFriendRepository
from src.domain.secret_friend.schemas import SecretFriendLink
from src.domain.secret_friend.service import SecretFriendService
from src.domain.secret_friend.signals import (
    secret_friend_assigned,
    secret_friend_deleted,
)


def _setup_group_with_two_participants(db_session: Session):
    """Helper: create a group and two participants, return (group, p1, p2)."""
    group = GroupService.create(
        GroupCreate(name="Handler Group", description="d"), db_session
    )
    p1 = ParticipantService.create(
        ParticipantCreate(name="Alice", group_id=group.id), db_session
    )
    p2 = ParticipantService.create(
        ParticipantCreate(name="Bob", group_id=group.id), db_session
    )
    return group, p1, p2


# ── Side-effect handler tests ────────────────────────────────────────────────


def test_on_secret_friend_assigned_logs_event(
    db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    from src.domain.secret_friend.handlers.side_effects import (
        _on_secret_friend_assigned,
        register_side_effects,
    )

    group, p1, p2 = _setup_group_with_two_participants(db_session)
    register_side_effects()
    try:
        with caplog.at_level(
            logging.INFO,
            logger="src.domain.secret_friend.handlers.side_effects",
        ):
            SecretFriendService.assign(
                group_id=group.id, participant_id=p1.id, db_session=db_session
            )

        assert any("secret friend assigned" in r.message for r in caplog.records)
    finally:
        secret_friend_assigned.disconnect(_on_secret_friend_assigned)


# ── Task relay handler tests ─────────────────────────────────────────────────


def test_relay_secret_friend_assigned_dispatches_task(db_session: Session) -> None:
    group, p1, p2 = _setup_group_with_two_participants(db_session)

    with patch(
        "src.domain.secret_friend.handlers.task_relays.dispatch_task"
    ) as mock_dispatch:
        from src.domain.secret_friend.handlers.task_relays import (
            _relay_secret_friend_assigned,
            register_task_relays,
        )

        register_task_relays()
        try:
            assignment = SecretFriendService.assign(
                group_id=group.id, participant_id=p1.id, db_session=db_session
            )
            mock_dispatch.assert_called_once_with(
                "notifications.secret_friend_assigned",
                assignment_id=assignment.id,
                group_id=group.id,
            )
        finally:
            secret_friend_assigned.disconnect(_relay_secret_friend_assigned)


def test_relay_secret_friend_deleted_dispatches_task(db_session: Session) -> None:
    group, p1, p2 = _setup_group_with_two_participants(db_session)

    assignment = SecretFriendRepository.link(
        SecretFriendLink(gift_giver_id=p1.id, gift_receiver_id=p2.id),
        db_session,
    )

    with patch(
        "src.domain.secret_friend.handlers.task_relays.dispatch_task"
    ) as mock_dispatch:
        from src.domain.secret_friend.handlers.task_relays import (
            _relay_secret_friend_deleted,
            register_task_relays,
        )

        register_task_relays()
        try:
            SecretFriendService.delete(assignment.id, db_session)
            mock_dispatch.assert_called_once_with(
                "notifications.secret_friend_deleted",
                secret_friend_id=assignment.id,
            )
        finally:
            secret_friend_deleted.disconnect(_relay_secret_friend_deleted)
