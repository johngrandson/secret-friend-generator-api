"""RunGatesUseCase — execute the harness gate runner, persist GateResults.

Caller (F7 OrchestrateRunUseCase) invokes after a successful execute step
(``Run.status == EXECUTED``). This use case:

1. Validates the Run is in EXECUTED.
2. Marks Run.status = GATES.
3. Runs the injected ``GateRunner`` against the workspace.
4. Persists every outcome as a ``GateResult`` row (single batch insert).
5. Settles via ``Run.complete_gates(all_passed=...)`` → GATES_PASSED / GATES_FAILED.

One commit at the end; events are pulled and published once after the
UoW context exits — same canonical pattern as ExecuteRunUseCase (F5).
"""

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from src.contexts.symphony.domain.gate_result.value_object import GateResult
from src.contexts.symphony.domain.harness_config import HarnessConfig
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.dto import RunDTO
from src.contexts.symphony.use_cases.run.errors import InvalidRunStateForGatesError
from src.contexts.symphony.use_cases.run.status_guards import (
    ensure_run_status,
    ensure_workspace_set,
)
from src.shared.agentic.gate import GateOutcome, GateRunner, GateStatus
from src.shared.event_publisher import IEventPublisher
from src.shared.events import DomainEvent


@dataclass
class RunGatesRequest:
    """Inputs for the gate run.

    ``harness_config`` is the domain-level VO consumed by gate adapters.
    Caller (F7 orchestrator) projects ``workflow.config.harness`` (the
    Pydantic schema) onto the domain VO via ``to_runtime()`` before
    handing it down here.
    """

    run_id: UUID
    harness_config: HarnessConfig


@dataclass
class RunGatesResponse:
    run: RunDTO | None
    all_passed: bool
    outcomes: list[GateOutcome]
    success: bool = True
    error_message: str | None = None


class RunGatesUseCase:
    """Run the harness gates against the workspace; persist verdicts."""

    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        gate_runner: GateRunner[HarnessConfig],
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._gate_runner = gate_runner
        self._publisher = event_publisher

    async def execute(self, request: RunGatesRequest) -> RunGatesResponse:
        response: RunGatesResponse
        events: list[DomainEvent] = []

        async with self._uow:
            run = await self._uow.runs.find_by_id(request.run_id)
            if run is None:
                return RunGatesResponse(
                    None,
                    False,
                    [],
                    success=False,
                    error_message="Run not found.",
                )
            ensure_run_status(
                run,
                RunStatus.EXECUTED,
                action="RunGates",
                error_class=InvalidRunStateForGatesError,
            )
            workspace_path = ensure_workspace_set(
                run, error_class=InvalidRunStateForGatesError
            )

            run.set_status(RunStatus.GATES)

            outcomes = await self._gate_runner.run_all(
                workspace=Path(workspace_path),
                config=request.harness_config,
            )
            results = [
                GateResult(
                    run_id=run.id,
                    gate_name=o.name,
                    status=o.status,
                    output=o.output,
                    duration_ms=o.duration_ms,
                )
                for o in outcomes
            ]
            await self._uow.gate_results.save_batch(results)

            all_passed = _compute_all_passed(outcomes)
            run.complete_gates(all_passed=all_passed)
            saved_run = await self._uow.runs.update(run)

            await self._uow.commit()
            events = run.pull_events()
            response = RunGatesResponse(
                run=RunDTO.from_entity(saved_run),
                all_passed=all_passed,
                outcomes=outcomes,
            )

        if events:
            await self._publisher.publish(events)
        return response


def _compute_all_passed(outcomes: list[GateOutcome]) -> bool:
    """Pass iff every non-skipped outcome is PASSED. No outcomes ⇒ pass."""
    non_skipped = [o for o in outcomes if o.status != GateStatus.SKIPPED]
    return all(o.status == GateStatus.PASSED for o in non_skipped)
