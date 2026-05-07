"""Unit tests for OpenPRUseCase: create vs update flow."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.agent_session.entity import AgentSession
from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.domain.code_host import CreatedPR, ExistingPR
from src.contexts.symphony.domain.gate_result.value_object import GateResult
from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.domain.pull_request.events import PROpened
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import RunCompleted
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.use_cases.run.open_pr import (
    InvalidRunStateForPRError,
    MissingArtifactError,
    OpenPRRequest,
    OpenPRUseCase,
)
from src.shared.agentic.agent_runner import TokenUsage
from src.shared.agentic.gate import GateName, GateStatus
from tests.conftest import FakePublisher, FakeSymphonyUoW


def _issue() -> Issue:
    return Issue(
        identifier="ENG-7",
        title="Build feature",
        description="d",
        priority=IssuePriority.MEDIUM,
        state="In Progress",
        branch_name=None,
        labels=(),
        created_at=datetime.now(timezone.utc),
        url=None,
    )


def _approved_spec(run_id) -> Spec:
    s = Spec.create(run_id=run_id, version=1, content="approved spec")
    s.approve(by="reviewer")
    s.pull_events()
    return s


def _approved_plan(run_id) -> Plan:
    p = Plan.create(run_id=run_id, version=1, content="approved plan")
    p.approve(by="reviewer")
    p.pull_events()
    return p


def _agent_session(run_id, *, model: str = "claude-sonnet-4-6") -> AgentSession:
    s = AgentSession.create(run_id=run_id, model=model)
    s.complete(usage=TokenUsage(input_tokens=10, output_tokens=2, total_tokens=12))
    s.pull_events()
    return s


def _gates_passed_run(workspace: Path) -> Run:
    run = Run.create(issue_id="ENG-7")
    for status in (
        RunStatus.GEN_SPEC,
        RunStatus.SPEC_PENDING,
        RunStatus.SPEC_APPROVED,
        RunStatus.GEN_PLAN,
        RunStatus.PLAN_PENDING,
        RunStatus.PLAN_APPROVED,
        RunStatus.EXECUTE,
        RunStatus.EXECUTED,
        RunStatus.GATES,
        RunStatus.GATES_PASSED,
    ):
        run.set_status(status, workspace_path=str(workspace))
    run.pull_events()
    return run


class _FakeCodeHost:
    def __init__(
        self,
        *,
        existing: ExistingPR | None = None,
        created: CreatedPR | None = None,
    ) -> None:
        self._existing = existing
        self._created = created or CreatedPR(
            number=42, url="https://x/pr/42"
        )
        self.calls: list[tuple[str, dict]] = []

    async def push_branch(self, *, branch: str, workspace: Path) -> None:
        self.calls.append(("push_branch", {"branch": branch, "workspace": workspace}))

    async def find_pr_for_branch(
        self, *, branch: str, workspace: Path
    ) -> ExistingPR | None:
        self.calls.append(("find", {"branch": branch}))
        return self._existing

    async def create_pr(self, **kwargs) -> CreatedPR:
        self.calls.append(("create_pr", kwargs))
        return self._created

    async def update_pr(self, **kwargs) -> None:
        self.calls.append(("update_pr", kwargs))


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


def _seed_uow(uow: FakeSymphonyUoW, run: Run) -> None:
    uow.runs.find_by_id.return_value = run
    uow.runs.update.side_effect = lambda r: r
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)
    uow.plans.find_latest_for_run.return_value = _approved_plan(run.id)
    uow.gate_results.find_by_run.return_value = [
        GateResult(
            run_id=run.id,
            gate_name=GateName("ci"),
            status=GateStatus.PASSED,
            output="ok",
            duration_ms=100,
        )
    ]
    uow.agent_sessions.list_by_run.return_value = [_agent_session(run.id)]
    uow.pull_requests.save.side_effect = lambda pr: pr
    uow.pull_requests.update.side_effect = lambda pr: pr


async def test_open_pr_creates_when_no_existing(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _gates_passed_run(tmp_path)
    _seed_uow(uow, run)
    code_host = _FakeCodeHost(existing=None)
    use_case = OpenPRUseCase(
        uow=uow, code_host=code_host, event_publisher=publisher
    )

    resp = await use_case.execute(
        OpenPRRequest(
            run_id=run.id,
            issue=_issue(),
            branch="agent/ENG-7",
            base_branch="main",
            title="agent: ENG-7",
            is_draft=True,
            labels=("agent",),
        )
    )

    assert resp.success is True
    assert resp.was_created is True
    assert resp.pr_number == 42
    assert resp.pr_url == "https://x/pr/42"
    assert run.status == RunStatus.DONE
    op_names = [c[0] for c in code_host.calls]
    assert op_names == ["push_branch", "find", "create_pr"]
    types = {type(e) for e in publisher.published}
    assert PROpened in types
    assert RunCompleted in types
    uow.pull_requests.save.assert_called_once()


async def test_open_pr_updates_when_existing(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _gates_passed_run(tmp_path)
    _seed_uow(uow, run)
    existing = ExistingPR(
        number=11, url="https://x/pr/11", is_draft=True
    )
    code_host = _FakeCodeHost(existing=existing)
    use_case = OpenPRUseCase(
        uow=uow, code_host=code_host, event_publisher=publisher
    )

    resp = await use_case.execute(
        OpenPRRequest(
            run_id=run.id,
            issue=_issue(),
            branch="agent/ENG-7",
            base_branch="main",
            title="agent: ENG-7",
        )
    )

    assert resp.was_created is False
    assert resp.pr_number == 11
    op_names = [c[0] for c in code_host.calls]
    assert "update_pr" in op_names
    assert "create_pr" not in op_names
    uow.pull_requests.update.assert_called_once()


async def test_open_pr_run_not_found(
    uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    uow.runs.find_by_id.return_value = None
    use_case = OpenPRUseCase(
        uow=uow, code_host=_FakeCodeHost(), event_publisher=publisher
    )
    resp = await use_case.execute(
        OpenPRRequest(
            run_id=uuid4(),
            issue=_issue(),
            branch="agent/x",
            base_branch="main",
            title="t",
        )
    )
    assert resp.success is False
    assert "not found" in (resp.error_message or "").lower()


async def test_open_pr_wrong_status_raises(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = Run.create(issue_id="ENG-7")
    run.set_status(RunStatus.GEN_SPEC, workspace_path=str(tmp_path))
    run.pull_events()
    uow.runs.find_by_id.return_value = run
    use_case = OpenPRUseCase(
        uow=uow, code_host=_FakeCodeHost(), event_publisher=publisher
    )
    with pytest.raises(InvalidRunStateForPRError):
        await use_case.execute(
            OpenPRRequest(
                run_id=run.id,
                issue=_issue(),
                branch="agent/x",
                base_branch="main",
                title="t",
            )
        )


async def test_open_pr_missing_approved_spec_raises(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _gates_passed_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    pending = Spec.create(run_id=run.id, version=1, content="pending")
    uow.specs.find_latest_for_run.return_value = pending  # not approved
    uow.plans.find_latest_for_run.return_value = _approved_plan(run.id)

    use_case = OpenPRUseCase(
        uow=uow, code_host=_FakeCodeHost(), event_publisher=publisher
    )
    with pytest.raises(MissingArtifactError, match="spec"):
        await use_case.execute(
            OpenPRRequest(
                run_id=run.id,
                issue=_issue(),
                branch="agent/x",
                base_branch="main",
                title="t",
            )
        )
