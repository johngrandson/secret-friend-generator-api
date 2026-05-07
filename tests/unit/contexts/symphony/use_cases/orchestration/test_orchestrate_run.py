"""Unit tests for OrchestrateRunUseCase — state-machine loop with re-read."""

from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.events import RunFailed
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.use_cases.orchestration.orchestrate_run import (
    OrchestrateOutcome,
    OrchestrateRunRequest,
    OrchestrateRunUseCase,
    OrchestrationContext,
    UnknownRunStatusError,
)
from tests.conftest import FakePublisher, FakeSymphonyUoW


def _issue() -> Issue:
    return Issue(
        identifier="ENG-9",
        title="Build feature",
        description="d",
        priority=IssuePriority.MEDIUM,
        state="In Progress",
        branch_name=None,
        labels=(),
        created_at=datetime.now(timezone.utc),
        url=None,
    )


def _ctx() -> OrchestrationContext:
    return OrchestrationContext(
        issue=_issue(),
        execute_prompt_template="${issue_identifier}: ${spec_content} ${plan_content}",
        model_name="claude-sonnet-4-6",
        harness_config=object(),
        pr_branch="agent/ENG-9",
        pr_base_branch="main",
        pr_title="agent: ENG-9",
        pr_is_draft=True,
        pr_labels=("agent",),
    )


class _ScriptedRunRepo:
    """Yields scripted Run states across find_by_id calls.

    Models persistence reads — each call to find_by_id returns the next
    Run state, simulating sub-use-cases having mutated the row.
    """

    def __init__(self, run_states: list[Run]) -> None:
        self._states = list(run_states)

    async def find_by_id(self, run_id):
        if not self._states:
            raise AssertionError("ScriptedRunRepo exhausted")
        return self._states.pop(0)

    update = AsyncMock()


def _run_at(status: RunStatus, *, workspace: str = "/tmp/ws") -> Run:
    run = Run.create(issue_id="ENG-9")
    run.workspace_path = workspace
    run.status = status
    run.pull_events()
    return run


@pytest.fixture
def publisher() -> FakePublisher:
    return FakePublisher()


def _make_use_case(
    uow: FakeSymphonyUoW, publisher: FakePublisher
) -> tuple[
    OrchestrateRunUseCase,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    AsyncMock,
    AsyncMock,
]:
    gen_spec = AsyncMock()
    gen_plan = AsyncMock()
    execute = AsyncMock()
    run_gates = AsyncMock()
    open_pr = AsyncMock()
    use_case = OrchestrateRunUseCase(
        uow=uow,
        generate_spec_use_case=gen_spec,
        generate_plan_use_case=gen_plan,
        execute_run_use_case=execute,
        run_gates_use_case=run_gates,
        open_pr_use_case=open_pr,
        event_publisher=publisher,
    )
    return use_case, gen_spec, gen_plan, execute, run_gates, open_pr


async def test_orchestrate_pauses_on_spec_pending(publisher) -> None:
    uow = FakeSymphonyUoW()
    uow.runs = _ScriptedRunRepo([_run_at(RunStatus.SPEC_PENDING)])
    use_case, gen_spec, *_ = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )

    assert resp.outcome == OrchestrateOutcome.PAUSED
    assert resp.paused_reason == "awaiting_spec_approval"
    gen_spec.execute.assert_not_called()


async def test_orchestrate_pauses_on_plan_pending(publisher) -> None:
    uow = FakeSymphonyUoW()
    uow.runs = _ScriptedRunRepo([_run_at(RunStatus.PLAN_PENDING)])
    use_case, *_ = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )

    assert resp.outcome == OrchestrateOutcome.PAUSED
    assert resp.paused_reason == "awaiting_plan_approval"


async def test_orchestrate_pauses_on_retry_pending(publisher) -> None:
    uow = FakeSymphonyUoW()
    uow.runs = _ScriptedRunRepo([_run_at(RunStatus.RETRY_PENDING)])
    use_case, *_ = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )

    assert resp.outcome == OrchestrateOutcome.PAUSED
    assert resp.paused_reason == "awaiting_retry"


async def test_orchestrate_completes_at_done(publisher) -> None:
    uow = FakeSymphonyUoW()
    uow.runs = _ScriptedRunRepo([_run_at(RunStatus.DONE)])
    use_case, *_ = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )
    assert resp.outcome == OrchestrateOutcome.COMPLETED
    assert resp.final_status == RunStatus.DONE.value


async def test_orchestrate_failed_terminates(publisher) -> None:
    uow = FakeSymphonyUoW()
    failed = _run_at(RunStatus.FAILED)
    failed.error = "boom"
    uow.runs = _ScriptedRunRepo([failed])
    use_case, *_ = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )
    assert resp.outcome == OrchestrateOutcome.FAILED
    assert resp.error_message == "boom"


async def test_orchestrate_gates_failed_marks_failed_and_emits(publisher) -> None:
    uow = FakeSymphonyUoW()
    gates_failed_run = _run_at(RunStatus.GATES_FAILED)
    final_run = _run_at(RunStatus.GATES_FAILED)
    # First read returns GATES_FAILED; second read (inside _mark_failed) returns same
    uow.runs = _ScriptedRunRepo([gates_failed_run, final_run])
    uow.runs.update = AsyncMock(side_effect=lambda r: r)
    use_case, *_ = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )
    assert resp.outcome == OrchestrateOutcome.FAILED
    assert resp.error_message == "gates_failed"
    types = {type(e) for e in publisher.published}
    assert RunFailed in types


async def test_orchestrate_dispatches_generate_spec_then_pauses(publisher) -> None:
    """First iteration runs GenerateSpec; second iteration sees SPEC_PENDING and pauses."""
    uow = FakeSymphonyUoW()
    uow.runs = _ScriptedRunRepo(
        [_run_at(RunStatus.GEN_SPEC), _run_at(RunStatus.SPEC_PENDING)]
    )
    use_case, gen_spec, *_ = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )
    assert resp.outcome == OrchestrateOutcome.PAUSED
    assert resp.paused_reason == "awaiting_spec_approval"
    gen_spec.execute.assert_awaited_once()


async def test_orchestrate_full_chain_terminates_done(publisher) -> None:
    """Walk SPEC_APPROVED → PLAN_APPROVED → EXECUTED → GATES_PASSED → DONE."""
    uow = FakeSymphonyUoW()
    uow.runs = _ScriptedRunRepo(
        [
            _run_at(RunStatus.SPEC_APPROVED),
            _run_at(RunStatus.PLAN_APPROVED),
            _run_at(RunStatus.EXECUTED),
            _run_at(RunStatus.GATES_PASSED),
            _run_at(RunStatus.DONE),
        ]
    )
    (
        use_case,
        gen_spec,
        gen_plan,
        execute,
        run_gates,
        open_pr,
    ) = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )

    assert resp.outcome == OrchestrateOutcome.COMPLETED
    gen_plan.execute.assert_awaited_once()
    execute.execute.assert_awaited_once()
    run_gates.execute.assert_awaited_once()
    open_pr.execute.assert_awaited_once()
    gen_spec.execute.assert_not_called()


async def test_orchestrate_run_not_found(publisher) -> None:
    uow = FakeSymphonyUoW()
    uow.runs = _ScriptedRunRepo([None])  # type: ignore[list-item]
    use_case, *_ = _make_use_case(uow, publisher)

    resp = await use_case.execute(
        OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
    )
    assert resp.outcome == OrchestrateOutcome.FAILED
    assert resp.error_message == "Run not found."


async def test_orchestrate_unknown_status_raises(publisher) -> None:
    uow = FakeSymphonyUoW()
    weird = _run_at(RunStatus.RECEIVED)  # RECEIVED is not handled
    uow.runs = _ScriptedRunRepo([weird])
    use_case, *_ = _make_use_case(uow, publisher)

    with pytest.raises(UnknownRunStatusError):
        await use_case.execute(
            OrchestrateRunRequest(run_id=uuid4(), context=_ctx())
        )
