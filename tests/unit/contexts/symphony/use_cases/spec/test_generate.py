"""Unit tests for GenerateSpecUseCase with fake AgentRunner / WorkspaceManager."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import RunStatusChanged
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.spec.events import SpecCreated
from src.contexts.symphony.use_cases.spec.generate import (
    GenerateSpecRequest,
    GenerateSpecUseCase,
    render_spec_prompt,
)
from src.shared.agentic.agent_runner import AgentRunnerError, TokenUsage, TurnResult
from src.shared.agentic.workspace import Workspace
from tests.conftest import FakePublisher, FakeSymphonyUoW

VALID_SPEC = """
## Goals
- foo

## Non-Goals
- bar

## Constraints
- baz

## Approach
- qux
"""


def _issue() -> Issue:
    return Issue(
        identifier="ENG-1",
        title="Add feature X",
        description="lengthy description",
        priority=IssuePriority.HIGH,
        state="In Progress",
        branch_name="feat/x",
        labels=("agent",),
        created_at=datetime.now(timezone.utc),
        url="https://example/issues/ENG-1",
    )


class _FakeWorkspaceManager:
    def __init__(self, *, root: Path, write_spec: bool = True) -> None:
        self._root = root
        self.write_spec = write_spec

    async def ensure(self, identifier: str) -> Workspace:
        path = self._root / identifier
        path.mkdir(parents=True, exist_ok=True)
        if self.write_spec:
            (path / ".symphony").mkdir(exist_ok=True)
            (path / ".symphony" / "spec.md").write_text(VALID_SPEC)
        return Workspace(path=path, key=identifier, created_now=True)

    async def run_hook(self, name, workspace):  # pragma: no cover
        return None

    async def cleanup(self, workspace):  # pragma: no cover
        pass


class _FakeAgentRunnerError(AgentRunnerError):
    """Test-local subclass to verify the narrowed except clause."""


class _FakeAgentRunner:
    def __init__(
        self,
        *,
        session_id: str = "sess-1",
        raises: Exception | None = None,
    ) -> None:
        self._session_id = session_id
        self._raises = raises
        self.run_turn_calls: list[dict] = []

    async def run_turn(
        self,
        *,
        prompt: str,
        workspace: Path,
        session_id: str | None = None,
    ) -> TurnResult:
        self.run_turn_calls.append(
            {
                "prompt": prompt,
                "workspace": workspace,
                "session_id": session_id,
            }
        )
        if self._raises is not None:
            raise self._raises
        return TurnResult(
            session_id=self._session_id,
            usage=TokenUsage(input_tokens=10, output_tokens=5, total_tokens=15),
            text="done",
        )


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    root = tmp_path / "ws"
    root.mkdir()
    return root


def _make_use_case(
    uow: FakeSymphonyUoW,
    publisher: FakePublisher,
    workspace_root: Path,
    *,
    write_spec: bool = True,
    runner_raises: Exception | None = None,
) -> tuple[GenerateSpecUseCase, _FakeAgentRunner, _FakeWorkspaceManager]:
    runner = _FakeAgentRunner(raises=runner_raises)
    manager = _FakeWorkspaceManager(root=workspace_root, write_spec=write_spec)
    use_case = GenerateSpecUseCase(
        uow=uow,
        agent_runner=runner,
        workspace_manager=manager,
        event_publisher=publisher,
    )
    return use_case, runner, manager


async def test_generate_spec_happy_path(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-1")
    uow.runs.find_by_id.return_value = run
    uow.specs.find_latest_for_run.return_value = None
    uow.specs.save.side_effect = lambda spec: spec

    use_case, runner, _ = _make_use_case(uow, publisher, workspace_root)

    resp = await use_case.execute(
        GenerateSpecRequest(run_id=run.id, issue=_issue())
    )

    assert resp.success is True
    assert resp.spec is not None
    assert resp.spec.run_id == run.id
    assert resp.spec.version == 1
    assert uow.committed is True
    assert run.status == RunStatus.SPEC_PENDING
    # First runner call uses the rendered prompt
    assert runner.run_turn_calls[0]["workspace"] == workspace_root / "ENG-1"
    assert "ENG-1" in runner.run_turn_calls[0]["prompt"]
    # Both Spec and Run events were published
    types = {type(e) for e in publisher.published}
    assert SpecCreated in types
    assert RunStatusChanged in types


async def test_generate_spec_increments_version_on_repeat(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-1")
    uow.runs.find_by_id.return_value = run
    previous_run_id = uuid4()
    from src.contexts.symphony.domain.spec.entity import Spec

    previous = Spec.create(run_id=previous_run_id, version=2, content="old")
    uow.specs.find_latest_for_run.return_value = previous
    uow.specs.save.side_effect = lambda spec: spec

    use_case, _, _ = _make_use_case(uow, publisher, workspace_root)

    resp = await use_case.execute(
        GenerateSpecRequest(run_id=run.id, issue=_issue())
    )

    assert resp.spec is not None
    assert resp.spec.version == 3


async def test_generate_spec_run_not_found(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    uow.runs.find_by_id.return_value = None
    use_case, _, _ = _make_use_case(uow, publisher, workspace_root)

    resp = await use_case.execute(
        GenerateSpecRequest(run_id=uuid4(), issue=_issue())
    )

    assert resp.success is False
    assert "Run not found" in (resp.error_message or "")
    uow.specs.save.assert_not_called()
    assert publisher.published == []


async def test_generate_spec_runner_failure(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-1")
    uow.runs.find_by_id.return_value = run
    use_case, _, _ = _make_use_case(
        uow, publisher, workspace_root,
        runner_raises=_FakeAgentRunnerError("CLI exploded"),
    )

    resp = await use_case.execute(
        GenerateSpecRequest(run_id=run.id, issue=_issue())
    )

    assert resp.success is False
    assert "CLI exploded" in (resp.error_message or "")
    uow.specs.save.assert_not_called()


async def test_generate_spec_missing_file(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-1")
    uow.runs.find_by_id.return_value = run
    use_case, _, _ = _make_use_case(uow, publisher, workspace_root, write_spec=False)

    resp = await use_case.execute(
        GenerateSpecRequest(run_id=run.id, issue=_issue())
    )

    assert resp.success is False
    assert "did not write" in (resp.error_message or "")
    uow.specs.save.assert_not_called()


async def test_generate_spec_malformed_content(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-1")
    uow.runs.find_by_id.return_value = run
    # Workspace writes spec.md but content is invalid (missing sections)
    bad_root = workspace_root
    bad_root.mkdir(parents=True, exist_ok=True)
    workdir = bad_root / "ENG-1"
    workdir.mkdir()
    (workdir / ".symphony").mkdir()
    (workdir / ".symphony" / "spec.md").write_text("just a paragraph, no headers")

    class _NoWriteWorkspace:
        async def ensure(self, identifier: str) -> Workspace:
            return Workspace(path=workdir, key=identifier, created_now=False)

        async def run_hook(self, name, workspace):  # pragma: no cover
            return None

        async def cleanup(self, workspace):  # pragma: no cover
            pass

    runner = _FakeAgentRunner()
    use_case = GenerateSpecUseCase(
        uow=uow,
        agent_runner=runner,
        workspace_manager=_NoWriteWorkspace(),
        event_publisher=publisher,
    )

    resp = await use_case.execute(
        GenerateSpecRequest(run_id=run.id, issue=_issue())
    )

    assert resp.success is False
    assert "missing required sections" in (resp.error_message or "")


def test_render_spec_prompt_substitutes_all_fields() -> None:
    rendered = render_spec_prompt(_issue())
    assert "ENG-1" in rendered
    assert "Add feature X" in rendered
    assert "HIGH" in rendered
    assert "agent" in rendered
    assert "lengthy description" in rendered
