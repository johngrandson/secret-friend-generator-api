"""GET /backlog/issues — list active issues from the configured tracker."""

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.backlog.deps import BacklogAdapterDep
from src.contexts.symphony.adapters.http.backlog.router import router
from src.contexts.symphony.adapters.http.backlog.serializers import (
    to_issue_output,
)
from src.contexts.symphony.domain.backlog.errors import BacklogAdapterError


@router.get("/issues")
async def list_active_issues(backlog: BacklogAdapterDep) -> list[dict]:
    """Return all active issues from the configured backlog tracker."""
    try:
        issues = await backlog.fetch_active_issues()
    except BacklogAdapterError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail=f"Backlog adapter failure: {exc}",
        ) from exc
    return [to_issue_output(issue) for issue in issues]
