"""IPullRequestRepository — output port (Protocol) for PR persistence."""

from typing import Protocol, runtime_checkable
from uuid import UUID

from src.contexts.symphony.domain.pull_request.entity import PullRequest


@runtime_checkable
class IPullRequestRepository(Protocol):
    """Structural interface for PullRequest persistence adapters."""

    async def find_by_id(self, pr_id: UUID) -> PullRequest | None: ...

    """Find a pull request by its ID."""

    async def find_for_run(self, run_id: UUID) -> PullRequest | None: ...

    """Find the pull request for a given run."""

    async def save(self, pr: PullRequest) -> PullRequest: ...

    """Save a new pull request."""

    async def update(self, pr: PullRequest) -> PullRequest: ...

    """Update an existing pull request."""
