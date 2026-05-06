"""Serialization helpers — RunDTO → JSON-serialisable dict."""

from src.contexts.symphony.use_cases.run.dto import RunDTO


def to_run_output(dto: RunDTO) -> dict:
    """Serialize a RunDTO to a plain dict for JSON responses."""
    return {
        "id": str(dto.id),
        "issue_id": dto.issue_id,
        "status": dto.status,
        "workspace_path": dto.workspace_path,
        "attempt": dto.attempt,
        "error": dto.error,
        "next_attempt_at": (
            dto.next_attempt_at.isoformat() if dto.next_attempt_at else None
        ),
        "created_at": dto.created_at.isoformat(),
    }
