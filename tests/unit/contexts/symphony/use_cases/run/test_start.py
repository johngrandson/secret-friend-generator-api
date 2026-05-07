"""Unit tests for StartRunUseCase."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.domain.run.events import RunStarted, RunStatusChanged
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.use_cases.run.start import (
    StartRunRequest,
    StartRunUseCase,
)
from src.shared.agentic.workspace import Workspace
from tests.conftest import FakePublisher, FakeSymphonyUoW


def _issue() -> Issue:
    return Issue(
        identifier="ENG-9",
        title="Build feature",
        description="desc",
        priority=IssuePriority.HIGH,
        state="In Progress",
        branch_name=None,
        labels=("agent",),
        created_at=datetime.now(timezone.utc),
        url="https://example/issue/ENG-9",
    )


class _FakeWorkspaceManager:
    def __init__(self, *, root: Path) -> None:
        self._root = root

    async def ensure(self, identifier: str) -> Workspace:
        path = self._root / identifier
        path.mkdir(parents=True, exist_ok=True)
        return Workspace(path=path, key=identifier, created_now=True)

    async def run_hook(self, name, workspace):  # pragma: no cover
        return None

    async def cleanup(self, workspace):  # pragma: no cover
        pass


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


async def test_start_run_creates_run_and_workspace(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    uow.runs.save.side_effect = lambda r: r
    use_case = StartRunUseCase(
        uow=uow,
        workspace_manager=_FakeWorkspaceManager(root=tmp_path),
        event_publisher=publisher,
    )

    resp = await use_case.execute(StartRunRequest(issue=_issue()))

    assert resp.success is True
    assert resp.run is not None
    assert resp.run.status == RunStatus.GEN_SPEC.value
    assert resp.workspace_path == str(tmp_path / "ENG-9")
    assert (tmp_path / "ENG-9").is_dir()
    assert uow.committed is True
    types = {type(e) for e in publisher.published}
    assert RunStarted in types
    assert RunStatusChanged in types
