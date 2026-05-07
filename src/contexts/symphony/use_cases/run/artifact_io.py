"""Shared filesystem helpers for spec/plan artifact reading.

Reads ``<workspace>/.symphony/<filename>`` and raises a caller-provided
exception when the agent did not produce the file. Two near-identical
private readers (``_read_spec_file`` / ``_read_plan_file``) collapsed
into one.

Filesystem I/O inside use_cases is a pre-existing trade-off in this
codebase — this helper consolidates it without introducing new violation.
"""

from pathlib import Path

from src.contexts.symphony.domain.constants import SYMPHONY_WORKSPACE_DIR


def read_artifact_file(
    *,
    workspace_root: Path,
    filename: str,
    missing_error: type[Exception],
    session_id: str | None,
) -> str:
    """Read the artifact text or raise ``missing_error`` with debug context."""
    artifact_path = workspace_root / SYMPHONY_WORKSPACE_DIR / filename
    if not artifact_path.is_file():
        raise missing_error(
            f"Agent did not write {artifact_path} (session_id={session_id})"
        )
    return artifact_path.read_text(encoding="utf-8")
