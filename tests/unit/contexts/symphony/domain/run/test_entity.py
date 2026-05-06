"""Unit tests for the Run aggregate entity."""

import pytest

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import (
    RunCompleted,
    RunFailed,
    RunStarted,
    RunStatusChanged,
)
from src.contexts.symphony.domain.run.status import RunStatus


def test_create_returns_run_with_issue_id():
    run = Run.create(issue_id="ENG-001")
    assert run.issue_id == "ENG-001"
    assert run.id is not None


def test_create_initial_status_is_received():
    run = Run.create(issue_id="ENG-001")
    assert run.status == RunStatus.RECEIVED


def test_create_collects_run_started_event():
    run = Run.create(issue_id="ENG-evt")
    events = run.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], RunStarted)
    assert events[0].run_id == run.id
    assert events[0].issue_id == "ENG-evt"


def test_create_blank_issue_id_raises():
    with pytest.raises(ValueError):
        Run.create(issue_id="   ")


def test_create_empty_issue_id_raises():
    with pytest.raises(ValueError):
        Run.create(issue_id="")


def test_pull_events_clears_after_read():
    run = Run.create(issue_id="ENG-001")
    run.pull_events()
    assert run.pull_events() == []


def test_set_status_transitions_and_collects_event():
    run = Run.create(issue_id="ENG-002")
    run.pull_events()  # clear RunStarted

    run.set_status(RunStatus.GEN_SPEC)

    assert run.status == RunStatus.GEN_SPEC
    events = run.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], RunStatusChanged)
    assert events[0].run_id == run.id
    assert events[0].from_status == "received"
    assert events[0].to_status == "gen_spec"


def test_set_status_same_status_is_noop():
    run = Run.create(issue_id="ENG-003")
    run.pull_events()  # clear RunStarted

    run.set_status(RunStatus.RECEIVED)  # already RECEIVED

    assert run.pull_events() == []


def test_set_status_updates_workspace_path():
    run = Run.create(issue_id="ENG-004")
    run.pull_events()

    run.set_status(RunStatus.EXECUTE, workspace_path="/workspaces/ENG-004")

    assert run.workspace_path == "/workspaces/ENG-004"


def test_set_status_without_workspace_path_leaves_it_unchanged():
    run = Run.create(issue_id="ENG-005")
    run.pull_events()

    run.set_status(RunStatus.GEN_SPEC)

    assert run.workspace_path is None


def test_mark_failed_sets_status_and_error():
    run = Run.create(issue_id="ENG-006")
    run.pull_events()

    run.mark_failed(error="Pipeline timed out.")

    assert run.status == RunStatus.FAILED
    assert run.error == "Pipeline timed out."


def test_mark_failed_collects_run_failed_event():
    run = Run.create(issue_id="ENG-007")
    run.pull_events()

    run.mark_failed(error="Connection refused.")

    events = run.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], RunFailed)
    assert events[0].run_id == run.id
    assert events[0].error == "Connection refused."
    assert events[0].attempt == run.attempt


def test_mark_failed_blank_error_raises():
    run = Run.create(issue_id="ENG-008")
    with pytest.raises(ValueError):
        run.mark_failed(error="   ")


def test_mark_failed_empty_error_raises():
    run = Run.create(issue_id="ENG-009")
    with pytest.raises(ValueError):
        run.mark_failed(error="")


def test_mark_completed_sets_status_done():
    run = Run.create(issue_id="ENG-010")
    run.pull_events()

    run.mark_completed()

    assert run.status == RunStatus.DONE


def test_mark_completed_collects_run_completed_event():
    run = Run.create(issue_id="ENG-011")
    run.pull_events()

    run.mark_completed()

    events = run.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], RunCompleted)
    assert events[0].run_id == run.id


def test_multiple_status_transitions_each_emit_event():
    run = Run.create(issue_id="ENG-012")
    run.pull_events()

    run.set_status(RunStatus.GEN_SPEC)
    run.set_status(RunStatus.SPEC_PENDING)

    events = run.pull_events()
    assert len(events) == 2
    assert isinstance(events[0], RunStatusChanged)
    assert events[0].to_status == "gen_spec"
    assert isinstance(events[1], RunStatusChanged)
    assert events[1].to_status == "spec_pending"
