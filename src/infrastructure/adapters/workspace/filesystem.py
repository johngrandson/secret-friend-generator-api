"""FilesystemWorkspaceManager — implements ``IWorkspaceManager`` on disk.

This module has zero git knowledge. It creates empty directories under
``workspace_root`` and runs operator-defined hooks (which typically
``git clone --depth 1 ...`` in ``after_create``). Per-issue isolation,
multi-repo support, and operator control all flow from that.

Hook failure policy:

    after_create  -> abort + rollback (rm -rf the partial dir) + raise
    before_run    -> abort + raise
    after_run     -> log and continue
    before_remove -> log and continue (about to delete anyway)
"""

import logging
import shutil
from pathlib import Path
from typing import Literal

from src.infrastructure.adapters.workflow import HooksConfig
from src.infrastructure.adapters.workspace.constants import (
    ABORT_ON_FAILURE_HOOKS,
    DEFAULT_HOOK_TIMEOUT_SECONDS,
    FALLBACK_KEY,
    MAX_KEY_LENGTH,
    UNSAFE_KEY_PATTERN,
)
from src.infrastructure.adapters.workspace.hooks import HookError, exec_hook
from src.shared.agentic.workspace import HookResult, ManagedHookName, Workspace

log = logging.getLogger(__name__)

AnyHookName = Literal["after_create", "before_run", "after_run", "before_remove"]


class WorkspaceError(Exception):
    """Base error for workspace-manager failures."""


class WorkspaceHookFailedError(WorkspaceError):
    """A hook with abort-on-failure policy returned non-zero."""

    def __init__(self, message: str, *, result: HookResult) -> None:
        super().__init__(message)
        self.result = result


def sanitize_workspace_key(identifier: str) -> str:
    """Replace unsafe filesystem chars with ``_``, truncate to ``MAX_KEY_LENGTH``.

    Empty input becomes the fallback ``_`` so a Workspace can always be
    constructed; callers should still validate the identifier upstream.
    """
    safe = UNSAFE_KEY_PATTERN.sub("_", identifier)
    return safe[:MAX_KEY_LENGTH] if safe else FALLBACK_KEY


class FilesystemWorkspaceManager:
    """Per-issue workspace lifecycle: ensure / run hook / cleanup."""

    def __init__(
        self,
        *,
        workspace_root: Path,
        hooks: HooksConfig,
        hook_timeout_seconds: float = DEFAULT_HOOK_TIMEOUT_SECONDS,
    ) -> None:
        self._root = workspace_root
        self._hooks = hooks
        self._timeout = hook_timeout_seconds

    async def ensure(self, identifier: str) -> Workspace:
        """Create the workspace if missing, run ``after_create`` on first creation.

        Idempotent: a second call with the same identifier returns the
        same path with ``created_now=False`` and does NOT re-run
        ``after_create``.

        Raises:
            WorkspaceHookFailedError: ``after_create`` returned non-zero.
                The partially-created directory is removed before the
                exception propagates.
            HookTimeoutError: ``after_create`` exceeded its timeout.
        """
        key = sanitize_workspace_key(identifier)
        path = self._root / key
        created_now = not path.exists()

        if created_now:
            path.mkdir(parents=True, exist_ok=False)
            log.info("workspace_created path=%s key=%s", path, key)

        workspace = Workspace(path=path, key=key, created_now=created_now)

        if created_now and self._hooks.after_create:
            try:
                await self._run_hook("after_create", workspace)
            except (WorkspaceHookFailedError, HookError):
                shutil.rmtree(path, ignore_errors=True)
                raise

        return workspace

    async def run_hook(
        self, name: ManagedHookName, workspace: Workspace
    ) -> HookResult | None:
        """Run ``before_run`` or ``after_run`` against ``workspace``.

        ``after_create`` and ``before_remove`` are managed internally by
        ``ensure`` and ``cleanup``; they are not callable here so the
        orchestrator cannot accidentally re-run them.

        Returns:
            The ``HookResult`` if the hook is configured, else ``None``.

        Raises:
            WorkspaceHookFailedError: only for ``before_run``.
                ``after_run`` failures are logged and swallowed.
            HookTimeoutError: hook exceeded its timeout.
        """
        return await self._run_hook(name, workspace)

    async def cleanup(self, workspace: Workspace) -> None:
        """Run ``before_remove`` (failure logged) and rm -rf the workspace.

        Never raises. Filesystem errors during the rm -rf are logged.
        """
        if self._hooks.before_remove:
            try:
                await self._run_hook("before_remove", workspace)
            except (WorkspaceHookFailedError, HookError) as err:
                log.warning(
                    "before_remove failed; continuing with cleanup path=%s err=%s",
                    workspace.path,
                    err,
                )

        shutil.rmtree(workspace.path, ignore_errors=True)
        log.info("workspace_cleaned_up path=%s", workspace.path)

    async def _run_hook(
        self, name: AnyHookName, workspace: Workspace
    ) -> HookResult | None:
        match name:
            case "after_create":
                script = self._hooks.after_create
            case "before_run":
                script = self._hooks.before_run
            case "after_run":
                script = self._hooks.after_run
            case "before_remove":
                script = self._hooks.before_remove
        if not script:
            return None

        result = await exec_hook(
            name=name,
            script=script,
            cwd=workspace.path,
            timeout_seconds=self._timeout,
        )

        if result.exit_code != 0:
            if name in ABORT_ON_FAILURE_HOOKS:
                raise WorkspaceHookFailedError(
                    f"Hook {name!r} exited with code {result.exit_code}: "
                    f"{result.output[:200]}",
                    result=result,
                )
            log.warning(
                "hook_failed_ignored name=%s exit=%d output=%s",
                name,
                result.exit_code,
                result.output[:200],
            )
        return result
