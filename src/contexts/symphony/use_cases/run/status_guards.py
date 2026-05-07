"""Reusable invariant guards for run-pipeline use cases.

Replaces three near-identical guard blocks in ``execute.py``, ``open_pr.py``
and ``run_gates.py`` (status-check + workspace-check + raise). Each
caller passes the exception class it wants raised so the public exception
contract from those modules stays unchanged.
"""

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus


def ensure_run_status(
    run: Run,
    expected: RunStatus,
    *,
    action: str,
    error_class: type[Exception],
) -> None:
    """Raise ``error_class`` when ``run.status`` is not ``expected``."""
    if run.status != expected:
        raise error_class(f"{action} requires status={expected.name}; got {run.status}")


def ensure_workspace_set(
    run: Run,
    *,
    error_class: type[Exception],
) -> str:
    """Return ``run.workspace_path`` or raise ``error_class`` when unset."""
    if run.workspace_path is None:
        raise error_class(
            "Run.workspace_path is not set; StartRunUseCase must run first."
        )
    return run.workspace_path
