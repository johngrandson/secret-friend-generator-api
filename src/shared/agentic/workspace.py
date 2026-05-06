"""IWorkspaceManager Protocol + Workspace VO — kernel workspace lifecycle.

A ``Workspace`` is a directory the agent operates inside. Concrete managers
(``FilesystemWorkspaceManager`` with hooks, future container-based managers)
live in ``src/infrastructure/adapters/`` and satisfy ``IWorkspaceManager``
structurally.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

ManagedHookName = Literal["before_run", "after_run"]


@dataclass(frozen=True)
class Workspace:
    """A directory the agent operates inside.

    ``created_now`` distinguishes the first call (where ``after_create`` runs)
    from idempotent subsequent calls. Callers pass this struct around as
    opaque state.
    """

    path: Path
    key: str
    created_now: bool

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("workspace key must not be empty")


@dataclass(frozen=True)
class HookResult:
    """Outcome of one hook subprocess invocation."""

    name: str
    exit_code: int
    output: str
    duration_ms: int = 0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("hook name must not be empty")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be >= 0")


@runtime_checkable
class IWorkspaceManager(Protocol):
    """Per-key workspace lifecycle: ensure / run hook / cleanup."""

    async def ensure(self, identifier: str) -> Workspace: ...

    async def run_hook(
        self, name: ManagedHookName, workspace: Workspace
    ) -> HookResult | None: ...

    async def cleanup(self, workspace: Workspace) -> None: ...
