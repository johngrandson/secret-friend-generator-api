"""Tests for group domain handlers (side-effects and task relays)."""

import logging
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from src.domain.group.schemas import GroupCreate, GroupUpdate
from src.domain.group.service import GroupService
from src.domain.group.signals import group_created, group_deleted, group_updated


# ── Side-effect handler tests ────────────────────────────────────────────────


def test_on_group_created_logs_event(
    db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    from src.domain.group.handlers.side_effects import (
        _on_group_created,
        register_side_effects,
    )

    register_side_effects()
    try:
        with caplog.at_level(logging.INFO, logger="src.domain.group.handlers.side_effects"):
            GroupService.create(GroupCreate(name="Log Test", description="d"), db_session)

        assert any("group created" in r.message for r in caplog.records)
    finally:
        group_created.disconnect(_on_group_created)


# ── Task relay handler tests ─────────────────────────────────────────────────


def test_relay_group_created_dispatches_task(db_session: Session) -> None:
    with patch("src.domain.group.handlers.task_relays.dispatch_task") as mock_dispatch:
        from src.domain.group.handlers.task_relays import (
            _relay_group_created,
            register_task_relays,
        )

        register_task_relays()
        try:
            group = GroupService.create(
                GroupCreate(name="Relay Group", description="d"), db_session
            )
            mock_dispatch.assert_called_once_with(
                "notifications.group_created",
                group_id=group.id,
                group_name="Relay Group",
            )
        finally:
            group_created.disconnect(_relay_group_created)


def test_relay_group_updated_dispatches_task(db_session: Session) -> None:
    group = GroupService.create(
        GroupCreate(name="Update Relay", description="d"), db_session
    )

    with patch("src.domain.group.handlers.task_relays.dispatch_task") as mock_dispatch:
        from src.domain.group.handlers.task_relays import (
            _relay_group_updated,
            register_task_relays,
        )

        register_task_relays()
        try:
            GroupService.update(group.id, GroupUpdate(name="Updated Relay"), db_session)
            mock_dispatch.assert_called_once_with(
                "notifications.group_updated",
                group_id=group.id,
                group_name="Updated Relay",
            )
        finally:
            group_updated.disconnect(_relay_group_updated)


def test_relay_group_deleted_dispatches_task(db_session: Session) -> None:
    group = GroupService.create(
        GroupCreate(name="Delete Relay", description="d"), db_session
    )

    with patch("src.domain.group.handlers.task_relays.dispatch_task") as mock_dispatch:
        from src.domain.group.handlers.task_relays import (
            _relay_group_deleted,
            register_task_relays,
        )

        register_task_relays()
        try:
            GroupService.delete(group.id, db_session)
            mock_dispatch.assert_called_once_with(
                "notifications.group_deleted", group_id=group.id
            )
        finally:
            group_deleted.disconnect(_relay_group_deleted)
