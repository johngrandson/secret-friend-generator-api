"""Unit tests for GeneratePlanUseCase with fake AgentRunner / WorkspaceManager."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.domain.plan.events import PlanCreated
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import RunStatusChanged
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.use_cases.plan.generate import (
    GeneratePlanRequest,
    GeneratePlanUseCase,
    render_plan_prompt,
)
from src.shared.agentic.agent_runner import AgentRunnerError, TokenUsage, TurnResult
from src.shared.agentic.workspace import Workspace
from tests.conftest import FakePublisher, FakeSymphonyUoW

VALID_PLAN = """
## Phases

### Phase 1: setup
**Goal:** scaffold

- [ ] add foo
- [ ] add bar
- [ ] wire deps
"""

VALID_SPEC_CONTENT = """
## Goals
- approved goal

## Non-Goals
- skip

## Constraints
- limit

## Approach
narrative
"""


def _issue() -> Issue:
    return Issue(
        identifier="ENG-2",
        title="Build feature Y",
        description="desc",
        priority=IssuePriority.MEDIUM,
        state="In Progress",
        branch_name=None,
        labels=(),
        created_at=datetime.now(timezone.utc),
        url=None,
    )


def _approved_spec(run_id) -> Spec:
    spec = Spec.create(run_id=run_id, version=1, content=VALID_SPEC_CONTENT)
    spec.approve(by="reviewer")
    spec.pull_events()  # discard create+approve events to keep test focused
    return spec


class _FakeWorkspaceManager:
    def __init__(self, *, root: Path, write_plan: bool = True) -> None:
        self._root = root
        self.write_plan = write_plan

    async def ensure(self, identifier: str) -> Workspace:
        path = self._root / identifier
        path.mkdir(parents=True, exist_ok=True)
        if self.write_plan:
            (path / ".symphony").mkdir(exist_ok=True)
            (path / ".symphony" / "plan.md").write_text(VALID_PLAN)
        return Workspace(path=path, key=identifier, created_now=True)

    async def run_hook(self, name, workspace):  # pragma: no cover
        return None

    async def cleanup(self, workspace):  # pragma: no cover
        pass


class _FakeAgentRunnerError(AgentRunnerError):
    """Test-local subclass to verify the narrowed except clause."""


class _FakeAgentRunner:
    def __init__(self, *, raises: Exception | None = None) -> None:
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
            {"prompt": prompt, "workspace": workspace, "session_id": session_id}
        )
        if self._raises is not None:
            raise self._raises
        return TurnResult(
            session_id="sess-x", usage=TokenUsage(), text="ok"
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
    write_plan: bool = True,
    runner_raises: Exception | None = None,
) -> tuple[GeneratePlanUseCase, _FakeAgentRunner]:
    runner = _FakeAgentRunner(raises=runner_raises)
    manager = _FakeWorkspaceManager(root=workspace_root, write_plan=write_plan)
    use_case = GeneratePlanUseCase(
        uow=uow,
        agent_runner=runner,
        workspace_manager=manager,
        event_publisher=publisher,
    )
    return use_case, runner


async def test_generate_plan_happy_path(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-2")
    uow.runs.find_by_id.return_value = run
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)
    uow.plans.find_latest_for_run.return_value = None
    uow.plans.save.side_effect = lambda plan: plan

    use_case, runner = _make_use_case(uow, publisher, workspace_root)

    resp = await use_case.execute(
        GeneratePlanRequest(run_id=run.id, issue=_issue())
    )

    assert resp.success is True
    assert resp.plan is not None
    assert resp.plan.version == 1
    assert run.status == RunStatus.PLAN_PENDING
    assert "approved goal" in runner.run_turn_calls[0]["prompt"]
    types = {type(e) for e in publisher.published}
    assert PlanCreated in types
    assert RunStatusChanged in types


async def test_generate_plan_run_not_found(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    uow.runs.find_by_id.return_value = None
    use_case, _ = _make_use_case(uow, publisher, workspace_root)

    resp = await use_case.execute(
        GeneratePlanRequest(run_id=uuid4(), issue=_issue())
    )

    assert resp.success is False
    assert "Run not found" in (resp.error_message or "")


async def test_generate_plan_no_approved_spec(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-2")
    uow.runs.find_by_id.return_value = run
    pending_spec = Spec.create(run_id=run.id, version=1, content=VALID_SPEC_CONTENT)
    uow.specs.find_latest_for_run.return_value = pending_spec  # not approved

    use_case, _ = _make_use_case(uow, publisher, workspace_root)

    resp = await use_case.execute(
        GeneratePlanRequest(run_id=run.id, issue=_issue())
    )

    assert resp.success is False
    assert "approved spec" in (resp.error_message or "").lower()
    uow.plans.save.assert_not_called()


async def test_generate_plan_increments_version(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-2")
    uow.runs.find_by_id.return_value = run
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)
    from src.contexts.symphony.domain.plan.entity import Plan

    previous = Plan.create(run_id=uuid4(), version=4, content="old")
    uow.plans.find_latest_for_run.return_value = previous
    uow.plans.save.side_effect = lambda plan: plan

    use_case, _ = _make_use_case(uow, publisher, workspace_root)

    resp = await use_case.execute(
        GeneratePlanRequest(run_id=run.id, issue=_issue())
    )

    assert resp.plan is not None
    assert resp.plan.version == 5


async def test_generate_plan_runner_failure(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-2")
    uow.runs.find_by_id.return_value = run
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)

    use_case, _ = _make_use_case(
        uow, publisher, workspace_root,
        runner_raises=_FakeAgentRunnerError("boom"),
    )

    resp = await use_case.execute(
        GeneratePlanRequest(run_id=run.id, issue=_issue())
    )

    assert resp.success is False
    assert "boom" in (resp.error_message or "")


async def test_generate_plan_invalid_structure(
    uow: FakeSymphonyUoW, publisher: FakePublisher, workspace_root: Path
) -> None:
    run = Run.create(issue_id="ENG-2")
    uow.runs.find_by_id.return_value = run
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)

    workdir = workspace_root / "ENG-2"
    workdir.mkdir()
    (workdir / ".symphony").mkdir()
    (workdir / ".symphony" / "plan.md").write_text("no phases header")

    class _PreWritten:
        async def ensure(self, identifier: str) -> Workspace:
            return Workspace(path=workdir, key=identifier, created_now=False)

        async def run_hook(self, name, workspace):  # pragma: no cover
            return None

        async def cleanup(self, workspace):  # pragma: no cover
            pass

    runner = _FakeAgentRunner()
    use_case = GeneratePlanUseCase(
        uow=uow,
        agent_runner=runner,
        workspace_manager=_PreWritten(),
        event_publisher=publisher,
    )

    resp = await use_case.execute(
        GeneratePlanRequest(run_id=run.id, issue=_issue())
    )

    assert resp.success is False
    assert "Phases" in (resp.error_message or "")


def test_render_plan_prompt_embeds_issue_and_spec() -> None:
    rendered = render_plan_prompt(
        issue=_issue(), approved_spec=VALID_SPEC_CONTENT
    )
    assert "ENG-2" in rendered
    assert "Build feature Y" in rendered
    assert "approved goal" in rendered
