"""CIGate — re-runs ``harness.ci_command`` as the canonical blocking gate.

The agent is supposed to have run CI in-session before declaring done; this
gate is the post-hoc sanity check that verifies the agent's claim against
fresh state. Reuses :func:`exec_hook` from the workspace adapter so
subprocess spawning, output capture (1MB cap, stderr merged), and timeout
handling stay in one place.

Output is truncated at :data:`MAX_OUTPUT_CHARS` to bound storage in
``GateOutcome`` / persisted ``gate_result`` rows. We truncate from the
*tail* — failing CI logs end with the actual error, so preserving the
last 5KB beats preserving the first.
"""

from pathlib import Path
from typing import ClassVar

from src.infrastructure.adapters.workflow import HarnessConfig
from src.infrastructure.adapters.workspace import HookTimeoutError, exec_hook
from src.shared.agentic.gate import Gate, GateName, GateOutcome, GateStatus

DEFAULT_CI_TIMEOUT_SECONDS = 1800.0  # 30 min
MAX_OUTPUT_CHARS = 5000

_GATE_NAME_CI = GateName("ci")


class CIGate(Gate[HarnessConfig]):
    """Run the operator's CI command and pass iff exit code is 0."""

    name: ClassVar[GateName] = _GATE_NAME_CI
    is_blocking: ClassVar[bool] = True

    def __init__(
        self, *, timeout_seconds: float = DEFAULT_CI_TIMEOUT_SECONDS
    ) -> None:
        self._timeout = timeout_seconds

    async def run(
        self, *, workspace: Path, config: HarnessConfig
    ) -> GateOutcome:
        try:
            result = await exec_hook(
                name="ci",
                script=config.ci_command,
                cwd=workspace,
                timeout_seconds=self._timeout,
            )
        except HookTimeoutError as err:
            return GateOutcome(
                name=self.name,
                status=GateStatus.FAILED,
                output=f"CI command timed out after {err.timeout_seconds}s",
                metadata_json={
                    "reason": "timeout",
                    "timeout_seconds": err.timeout_seconds,
                },
                duration_ms=int(err.timeout_seconds * 1000),
            )

        status = (
            GateStatus.PASSED if result.exit_code == 0 else GateStatus.FAILED
        )
        output = _truncate_tail(result.output, MAX_OUTPUT_CHARS)
        return GateOutcome(
            name=self.name,
            status=status,
            output=output,
            metadata_json={"exit_code": result.exit_code},
            duration_ms=result.duration_ms,
        )


def _truncate_tail(output: str, max_chars: int) -> str:
    if len(output) <= max_chars:
        return output
    marker = "\n[...truncated head...]\n"
    keep = max_chars - len(marker)
    return marker + output[-keep:]
