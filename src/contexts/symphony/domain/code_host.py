"""ICodeHost — output port Protocol for code-hosting integrations.

``ICodeHost`` is the symphony-context port any code-host adapter must
satisfy (today: ``GitHubCodeHost``; potential: ``GitLabCodeHost``,
``BitbucketCodeHost``). The port is symphony-specific (PR/branch/diff
semantics) — not lifted to ``shared/agentic/`` because non-devops
verticals (research agents, autonomous QA, data extraction) have no
notion of pull requests.

VOs ``ExistingPR`` and ``CreatedPR`` carry the minimum fields the
orchestrator needs after a host operation.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


class CodeHostError(Exception):
    """Base error for any code-host adapter failure."""


class CodeHostBinaryNotFoundError(CodeHostError):
    """The required CLI binary (``gh``, ``glab``, ``git``) is not on PATH."""


class CodeHostCommandError(CodeHostError):
    """A code-host CLI command returned a non-zero exit status."""

    def __init__(
        self, message: str, *, exit_code: int, stdout: str, stderr: str
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


@dataclass(frozen=True)
class CreatedPR:
    """Outcome of a fresh ``create_pr`` call."""

    number: int
    url: str

    def __post_init__(self) -> None:
        if self.number < 0:
            raise ValueError("PR number must be >= 0")
        if not self.url.strip():
            raise ValueError("PR url must not be blank")


@dataclass(frozen=True)
class ExistingPR:
    """An open PR already attached to a branch."""

    number: int
    url: str
    is_draft: bool

    def __post_init__(self) -> None:
        if self.number < 0:
            raise ValueError("PR number must be >= 0")
        if not self.url.strip():
            raise ValueError("PR url must not be blank")


@runtime_checkable
class ICodeHost(Protocol):
    """Port for any code-host integration. Async + stateless beyond config."""

    async def push_branch(self, *, branch: str, workspace: Path) -> None:
        """Push ``branch`` from ``workspace`` to the host's ``origin`` remote.

        Raises :class:`CodeHostCommandError` on non-zero exit (auth / conflict).
        """
        ...

    async def find_pr_for_branch(
        self, *, branch: str, workspace: Path
    ) -> ExistingPR | None:
        """Look up the open PR (if any) whose head matches ``branch``."""
        ...

    async def create_pr(
        self,
        *,
        branch: str,
        base: str,
        title: str,
        body: str,
        labels: Sequence[str],
        draft: bool,
        workspace: Path,
    ) -> CreatedPR:
        """Open a fresh PR. Raises :class:`CodeHostCommandError` on failure."""
        ...

    async def update_pr(
        self, *, pr_number: int, title: str, body: str, workspace: Path
    ) -> None:
        """Refresh title and body on an existing PR."""
        ...
