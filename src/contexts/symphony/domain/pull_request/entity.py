"""PullRequest aggregate root — one PR per Run."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.contexts.symphony.domain.pull_request.events import (
    PROpened,
    PRUpdated,
)
from src.shared.aggregate_root import AggregateRoot


@dataclass
class PullRequest(AggregateRoot):
    """Aggregate root representing the GitHub PR opened for a Run."""

    run_id: UUID
    number: int
    url: str
    branch: str
    base_branch: str
    is_draft: bool = True
    body: str = ""
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def mark_ready(self) -> None:
        """Flip from draft to ready-for-review; emits PRUpdated."""
        if not self.is_draft:
            return
        self.is_draft = False
        self.collect_event(
            PRUpdated(pr_id=self.id, run_id=self.run_id, number=self.number)
        )

    def update_body(self, body: str) -> None:
        """Replace the PR body text; emits PRUpdated."""
        if body == self.body:
            return
        self.body = body
        self.collect_event(
            PRUpdated(pr_id=self.id, run_id=self.run_id, number=self.number)
        )

    @classmethod
    def open(
        cls,
        *,
        run_id: UUID,
        number: int,
        url: str,
        branch: str,
        base_branch: str,
        is_draft: bool = True,
        body: str = "",
    ) -> "PullRequest":
        """Factory — validates non-empty fields and emits PROpened."""
        if number < 1:
            raise ValueError("PR number must be >= 1.")
        for name, value in (
            ("url", url),
            ("branch", branch),
            ("base_branch", base_branch),
        ):
            if not value.strip():
                raise ValueError(f"PR {name} must not be blank.")
        pr = cls(
            run_id=run_id,
            number=number,
            url=url,
            branch=branch,
            base_branch=base_branch,
            is_draft=is_draft,
            body=body,
        )
        pr.collect_event(
            PROpened(pr_id=pr.id, run_id=run_id, number=number, url=url)
        )
        return pr
