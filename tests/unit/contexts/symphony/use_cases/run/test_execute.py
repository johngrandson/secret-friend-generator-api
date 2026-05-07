"""Unit tests for ExecuteRunUseCase: happy path + retry + terminal failure."""

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from src.contexts.symphony.domain.agent_session.events import (
    AgentSessionCompleted,
    AgentSessionFailed,
)
from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import RunExecuted
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.use_cases.run.execute import (
    ExecuteOutcome,
    ExecuteRunRequest,
    ExecuteRunUseCase,
    InvalidRunStateError,
)
from src.shared.agentic.agent_runner import (
    AgentRunnerError,
    TokenUsage,
    TurnResult,
)
from src.shared.agentic.retry import (
    AgentTerminalError,
    AgentTransientStallError,
    RetryConfig,
)
from tests.conftest import FakePublisher, FakeSymphonyUoW

PROMPT_TEMPLATE = (
    "Issue ${issue_identifier}: ${issue_title}\n"
    "Approved spec:\n${spec_content}\n\nApproved plan:\n${plan_content}\n"
    "Attempt ${attempt}"
)


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
    s = Spec.create(run_id=run_id, version=1, content="approved spec body")
    s.approve(by="reviewer")
    s.pull_events()
    return s


def _approved_plan(run_id) -> Plan:
    p = Plan.create(run_id=run_id, version=1, content="approved plan body")
    p.approve(by="reviewer")
    p.pull_events()
    return p


def _make_run(workspace: Path) -> Run:
    run = Run.create(issue_id="ENG-7")
    run.set_status(RunStatus.GEN_SPEC, workspace_path=str(workspace))
    run.set_status(RunStatus.SPEC_PENDING)
    run.set_status(RunStatus.SPEC_APPROVED)
    run.set_status(RunStatus.GEN_PLAN)
    run.set_status(RunStatus.PLAN_PENDING)
    run.set_status(RunStatus.PLAN_APPROVED)
    run.pull_events()
    return run


class _FakeAgentRunner:
    def __init__(
        self,
        *,
        result: TurnResult | None = None,
        raises: Exception | None = None,
    ) -> None:
        self._result = result
        self._raises = raises
        self.calls: list[dict] = []

    async def run_turn(
        self,
        *,
        prompt: str,
        workspace: Path,
        session_id: str | None = None,
    ) -> TurnResult:
        self.calls.append(
            {"prompt": prompt, "workspace": workspace, "session_id": session_id}
        )
        if self._raises is not None:
            raise self._raises
        assert self._result is not None
        return self._result


@pytest.fixture
def uow() -> FakeSymphonyUoW:
    return FakeSymphonyUoW()


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


async def test_execute_run_happy_path(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _make_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    uow.runs.update.side_effect = lambda r: r
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)
    uow.plans.find_latest_for_run.return_value = _approved_plan(run.id)
    uow.agent_sessions.save.side_effect = lambda s: s

    runner = _FakeAgentRunner(
        result=TurnResult(
            session_id="sess-1",
            usage=TokenUsage(input_tokens=10, output_tokens=4, total_tokens=14),
            text="done",
        )
    )
    use_case = ExecuteRunUseCase(uow=uow, agent_runner=runner, event_publisher=publisher)

    resp = await use_case.execute(
        ExecuteRunRequest(
            run_id=run.id,
            issue=_issue(),
            prompt_template=PROMPT_TEMPLATE,
            model_name="claude-sonnet-4-6",
        )
    )

    assert resp.outcome == ExecuteOutcome.SUCCESS
    assert resp.session_id == "sess-1"
    assert run.status == RunStatus.EXECUTED
    assert "approved spec body" in runner.calls[0]["prompt"]
    assert "approved plan body" in runner.calls[0]["prompt"]
    types = {type(e) for e in publisher.published}
    assert RunExecuted in types
    assert AgentSessionCompleted in types


async def test_execute_run_retry_on_transient_stall(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _make_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    uow.runs.update.side_effect = lambda r: r
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)
    uow.plans.find_latest_for_run.return_value = _approved_plan(run.id)
    uow.agent_sessions.save.side_effect = lambda s: s

    runner = _FakeAgentRunner(
        raises=AgentTransientStallError("stalled mid-turn")
    )
    use_case = ExecuteRunUseCase(uow=uow, agent_runner=runner, event_publisher=publisher)

    resp = await use_case.execute(
        ExecuteRunRequest(
            run_id=run.id,
            issue=_issue(),
            prompt_template=PROMPT_TEMPLATE,
            model_name="claude-sonnet-4-6",
            retry_config=RetryConfig(continuation_delay_ms=2000),
        )
    )

    assert resp.outcome == ExecuteOutcome.RETRY_PENDING
    assert run.status == RunStatus.RETRY_PENDING
    assert run.next_attempt_at is not None
    assert run.next_attempt_at > datetime.now(timezone.utc)
    assert AgentSessionFailed in {type(e) for e in publisher.published}


async def test_execute_run_terminal_marks_failed(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _make_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    uow.runs.update.side_effect = lambda r: r
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)
    uow.plans.find_latest_for_run.return_value = _approved_plan(run.id)
    uow.agent_sessions.save.side_effect = lambda s: s

    runner = _FakeAgentRunner(
        raises=AgentTerminalError("operator must intervene")
    )
    use_case = ExecuteRunUseCase(uow=uow, agent_runner=runner, event_publisher=publisher)

    resp = await use_case.execute(
        ExecuteRunRequest(
            run_id=run.id,
            issue=_issue(),
            prompt_template=PROMPT_TEMPLATE,
            model_name="claude-sonnet-4-6",
        )
    )

    assert resp.outcome == ExecuteOutcome.FAILED
    assert run.status == RunStatus.FAILED


async def test_execute_run_unknown_runner_error_is_retryable(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    """A subclass of AgentRunnerError without retry markers gets ``failure`` kind."""
    run = _make_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    uow.runs.update.side_effect = lambda r: r
    uow.specs.find_latest_for_run.return_value = _approved_spec(run.id)
    uow.plans.find_latest_for_run.return_value = _approved_plan(run.id)
    uow.agent_sessions.save.side_effect = lambda s: s

    runner = _FakeAgentRunner(raises=AgentRunnerError("boom"))
    use_case = ExecuteRunUseCase(uow=uow, agent_runner=runner, event_publisher=publisher)

    resp = await use_case.execute(
        ExecuteRunRequest(
            run_id=run.id,
            issue=_issue(),
            prompt_template=PROMPT_TEMPLATE,
            model_name="claude-sonnet-4-6",
        )
    )

    assert resp.outcome == ExecuteOutcome.RETRY_PENDING
    assert run.status == RunStatus.RETRY_PENDING


async def test_execute_run_run_not_found(
    uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    uow.runs.find_by_id.return_value = None
    runner = _FakeAgentRunner(result=TurnResult(session_id="x"))
    use_case = ExecuteRunUseCase(uow=uow, agent_runner=runner, event_publisher=publisher)

    resp = await use_case.execute(
        ExecuteRunRequest(
            run_id=uuid4(),
            issue=_issue(),
            prompt_template="t",
            model_name="claude-sonnet-4-6",
        )
    )
    assert resp.outcome == ExecuteOutcome.FAILED
    assert "Run not found" in (resp.error_message or "")


async def test_execute_run_wrong_status_raises(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = Run.create(issue_id="ENG-X")
    run.set_status(RunStatus.GEN_SPEC, workspace_path=str(tmp_path))
    run.pull_events()
    uow.runs.find_by_id.return_value = run

    runner = _FakeAgentRunner(result=TurnResult(session_id="x"))
    use_case = ExecuteRunUseCase(uow=uow, agent_runner=runner, event_publisher=publisher)

    with pytest.raises(InvalidRunStateError):
        await use_case.execute(
            ExecuteRunRequest(
                run_id=run.id,
                issue=_issue(),
                prompt_template="t",
                model_name="claude-sonnet-4-6",
            )
        )


async def test_execute_run_no_approved_spec(
    tmp_path: Path, uow: FakeSymphonyUoW, publisher: FakePublisher
) -> None:
    run = _make_run(tmp_path)
    uow.runs.find_by_id.return_value = run
    pending = Spec.create(run_id=run.id, version=1, content="pending")
    uow.specs.find_latest_for_run.return_value = pending  # not approved

    runner = _FakeAgentRunner(result=TurnResult(session_id="x"))
    use_case = ExecuteRunUseCase(uow=uow, agent_runner=runner, event_publisher=publisher)

    resp = await use_case.execute(
        ExecuteRunRequest(
            run_id=run.id,
            issue=_issue(),
            prompt_template="t",
            model_name="claude-sonnet-4-6",
        )
    )
    assert resp.outcome == ExecuteOutcome.FAILED
    assert "approved spec" in (resp.error_message or "").lower()
