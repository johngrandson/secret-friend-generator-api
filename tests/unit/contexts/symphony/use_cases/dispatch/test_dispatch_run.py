"""Unit tests for DispatchRunUseCase: BUSY/IDLE/DISPATCHED_NEW/DISPATCHED_RETRY."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.use_cases.dispatch.dispatch_run import (
    DispatchOutcome,
    DispatchRunRequest,
    DispatchRunUseCase,
)
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.run.start import StartRunResponse
from tests.conftest import FakePublisher, FakeSymphonyUoW


def _issue(identifier: str, *, priority: IssuePriority = IssuePriority.MEDIUM) -> Issue:
    return Issue(
        identifier=identifier,
        title=f"Issue {identifier}",
        description="",
        priority=priority,
        state="In Progress",
        branch_name=None,
        labels=(),
        created_at=datetime.now(timezone.utc),
        url=None,
    )


class _FakeBacklog:
    def __init__(self, issues: list[Issue]) -> None:
        self._issues = issues
        self.calls = 0

    async def fetch_active_issues(self) -> list[Issue]:
        self.calls += 1
        return list(self._issues)

    async def fetch_issue(self, identifier):  # pragma: no cover
        return None

    async def fetch_terminal_issues_since(self, since):  # pragma: no cover
        return []

    async def post_comment(self, identifier, body):  # pragma: no cover
        return None

    async def aclose(self):  # pragma: no cover
        return None

    def is_terminal(self, state: str) -> bool:  # pragma: no cover
        return False


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


@pytest.fixture
def start_run() -> AsyncMock:
    return AsyncMock()


def _make_use_case(
    uow: FakeSymphonyUoW, publisher: FakePublisher, start_run: AsyncMock
) -> DispatchRunUseCase:
    return DispatchRunUseCase(
        uow=uow, start_run_use_case=start_run, event_publisher=publisher
    )


async def test_dispatch_busy_when_at_concurrency_cap(
    uow: FakeSymphonyUoW, publisher: FakePublisher, start_run: AsyncMock
) -> None:
    uow.runs.count_active.return_value = 5
    backlog = _FakeBacklog([])
    use_case = _make_use_case(uow, publisher, start_run)

    resp = await use_case.execute(
        DispatchRunRequest(backlog=backlog, max_concurrent=5)
    )

    assert resp.outcome == DispatchOutcome.BUSY
    assert resp.run_id is None
    start_run.execute.assert_not_called()
    assert backlog.calls == 0


async def test_dispatch_idle_when_no_eligible_issues(
    uow: FakeSymphonyUoW, publisher: FakePublisher, start_run: AsyncMock
) -> None:
    uow.runs.count_active.return_value = 0
    uow.runs.find_due_retries.return_value = []
    uow.runs.list_active_identifiers.return_value = []
    backlog = _FakeBacklog([])
    use_case = _make_use_case(uow, publisher, start_run)

    resp = await use_case.execute(
        DispatchRunRequest(backlog=backlog, max_concurrent=5)
    )

    assert resp.outcome == DispatchOutcome.IDLE
    start_run.execute.assert_not_called()


async def test_dispatch_skips_already_active_identifiers(
    uow: FakeSymphonyUoW, publisher: FakePublisher, start_run: AsyncMock
) -> None:
    uow.runs.count_active.return_value = 1
    uow.runs.find_due_retries.return_value = []
    uow.runs.list_active_identifiers.return_value = ["ENG-1"]
    backlog = _FakeBacklog([_issue("ENG-1"), _issue("ENG-2")])

    start_run.execute.return_value = StartRunResponse(
        run=RunDTO(
            id=uuid_helper(),
            issue_id="ENG-2",
            status=RunStatus.GEN_SPEC.value,
            workspace_path="/tmp/ws/ENG-2",
            attempt=1,
            error=None,
            next_attempt_at=None,
            created_at=datetime.now(timezone.utc),
        ),
        workspace_path="/tmp/ws/ENG-2",
        success=True,
    )

    use_case = _make_use_case(uow, publisher, start_run)
    resp = await use_case.execute(
        DispatchRunRequest(backlog=backlog, max_concurrent=5)
    )

    assert resp.outcome == DispatchOutcome.DISPATCHED_NEW
    assert resp.issue_identifier == "ENG-2"
    start_run.execute.assert_awaited_once()


async def test_dispatch_picks_highest_priority(
    uow: FakeSymphonyUoW, publisher: FakePublisher, start_run: AsyncMock
) -> None:
    uow.runs.count_active.return_value = 0
    uow.runs.find_due_retries.return_value = []
    uow.runs.list_active_identifiers.return_value = []
    issues = [
        _issue("LOW-1", priority=IssuePriority.LOW),
        _issue("URGENT-1", priority=IssuePriority.URGENT),
        _issue("MED-1", priority=IssuePriority.MEDIUM),
    ]
    backlog = _FakeBacklog(issues)
    start_run.execute.return_value = StartRunResponse(
        run=RunDTO(
            id=uuid_helper(),
            issue_id="URGENT-1",
            status=RunStatus.GEN_SPEC.value,
            workspace_path="/tmp/ws",
            attempt=1,
            error=None,
            next_attempt_at=None,
            created_at=datetime.now(timezone.utc),
        ),
        workspace_path="/tmp/ws",
        success=True,
    )

    use_case = _make_use_case(uow, publisher, start_run)
    resp = await use_case.execute(
        DispatchRunRequest(backlog=backlog, max_concurrent=5)
    )

    assert resp.outcome == DispatchOutcome.DISPATCHED_NEW
    assert resp.issue_identifier == "URGENT-1"


async def test_dispatch_due_retry_takes_precedence(
    uow: FakeSymphonyUoW, publisher: FakePublisher, start_run: AsyncMock
) -> None:
    """When both due retries AND fresh issues exist, retry wins."""
    uow.runs.count_active.return_value = 0
    retry_run = Run.create(issue_id="ENG-99")
    retry_run.set_status(RunStatus.GEN_SPEC)
    retry_run.set_status(RunStatus.SPEC_PENDING)
    retry_run.set_status(RunStatus.SPEC_APPROVED)
    retry_run.set_status(RunStatus.GEN_PLAN)
    retry_run.set_status(RunStatus.PLAN_PENDING)
    retry_run.set_status(RunStatus.PLAN_APPROVED)
    retry_run.mark_retry_pending(
        error="stalled",
        next_attempt_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    retry_run.pull_events()
    uow.runs.find_due_retries.return_value = [retry_run]
    uow.runs.update.side_effect = lambda r: r

    backlog = _FakeBacklog([_issue("FRESH-1")])
    use_case = _make_use_case(uow, publisher, start_run)
    resp = await use_case.execute(
        DispatchRunRequest(backlog=backlog, max_concurrent=5)
    )

    assert resp.outcome == DispatchOutcome.DISPATCHED_RETRY
    assert resp.issue_identifier == "ENG-99"
    assert retry_run.status == RunStatus.PLAN_APPROVED  # resumed
    assert retry_run.attempt == 2
    start_run.execute.assert_not_called()
    assert backlog.calls == 0  # never queried


async def test_dispatch_invalid_max_concurrent_raises(
    uow: FakeSymphonyUoW, publisher: FakePublisher, start_run: AsyncMock
) -> None:
    use_case = _make_use_case(uow, publisher, start_run)
    with pytest.raises(ValueError, match="max_concurrent"):
        await use_case.execute(
            DispatchRunRequest(backlog=_FakeBacklog([]), max_concurrent=0)
        )


# Helpers ---------------------------------------------------------------


def uuid_helper():
    from uuid import uuid4

    return uuid4()
