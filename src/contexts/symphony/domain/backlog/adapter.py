"""IBacklogAdapter — output port Protocol for backlog tracker integrations."""

from datetime import datetime
from typing import Protocol, runtime_checkable

from src.contexts.symphony.domain.backlog.issue import Issue


@runtime_checkable
class IBacklogAdapter(Protocol):
    """Structural interface for any backlog tracker adapter (e.g. Linear, Jira)."""

    async def fetch_active_issues(self) -> list[Issue]:
        """Fetch all active issues from the backlog tracker."""
        ...

    async def fetch_issue(self, identifier: str) -> Issue | None:
        """Fetch a specific issue by identifier."""
        ...

    async def post_comment(self, identifier: str, body: str) -> None:
        """Post a comment to a specific issue."""
        ...

    async def aclose(self) -> None:
        """Close the adapter connection."""
        ...

    async def fetch_terminal_issues_since(self, since: datetime) -> list[Issue]:
        """Fetch issues that reached a terminal state after the given datetime."""
        ...

    def is_terminal(self, state: str) -> bool:
        """Return True if the given state name is a terminal (done/cancelled) state."""
        ...
