"""Workspace adapter — filesystem-based ``IWorkspaceManager`` impl + hooks.

The manager creates empty workspaces, runs operator-supplied hooks
(typically ``git clone ...`` in ``after_create``), and cleans up on
terminal issues. No git knowledge lives here — operators control source
acquisition entirely through WORKFLOW.md hooks.
"""

from src.infrastructure.adapters.workspace.filesystem import (
    MAX_KEY_LENGTH,
    FilesystemWorkspaceManager,
    WorkspaceError,
    WorkspaceHookFailedError,
    sanitize_workspace_key,
)
from src.infrastructure.adapters.workspace.hooks import (
    DEFAULT_HOOK_TIMEOUT_SECONDS,
    HookError,
    HookTimeoutError,
    exec_hook,
)

__all__ = [
    "DEFAULT_HOOK_TIMEOUT_SECONDS",
    "MAX_KEY_LENGTH",
    "FilesystemWorkspaceManager",
    "HookError",
    "HookTimeoutError",
    "WorkspaceError",
    "WorkspaceHookFailedError",
    "exec_hook",
    "sanitize_workspace_key",
]
