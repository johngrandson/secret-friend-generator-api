"""Unit tests for FilesystemWorkspaceManager + exec_hook."""

from pathlib import Path

import pytest

from src.infrastructure.adapters.workflow import HooksConfig
from src.infrastructure.adapters.workspace import (
    FilesystemWorkspaceManager,
    HookTimeoutError,
    WorkspaceHookFailedError,
    exec_hook,
    sanitize_workspace_key,
)


def _empty_hooks() -> HooksConfig:
    return HooksConfig()


def test_sanitize_workspace_key_replaces_unsafe_chars() -> None:
    assert sanitize_workspace_key("ENG-123") == "ENG-123"
    assert sanitize_workspace_key("foo/bar baz") == "foo_bar_baz"
    assert sanitize_workspace_key("../escape") == ".._escape"


def test_sanitize_workspace_key_truncates() -> None:
    big = "a" * 200
    assert len(sanitize_workspace_key(big)) == 64


def test_sanitize_workspace_key_empty_falls_back() -> None:
    assert sanitize_workspace_key("") == "_"


@pytest.mark.asyncio
async def test_ensure_creates_directory_and_returns_workspace(
    tmp_path: Path,
) -> None:
    manager = FilesystemWorkspaceManager(
        workspace_root=tmp_path, hooks=_empty_hooks()
    )
    ws = await manager.ensure("ENG-123")
    assert ws.path == tmp_path / "ENG-123"
    assert ws.path.is_dir()
    assert ws.created_now is True
    assert ws.key == "ENG-123"


@pytest.mark.asyncio
async def test_ensure_is_idempotent(tmp_path: Path) -> None:
    manager = FilesystemWorkspaceManager(
        workspace_root=tmp_path, hooks=_empty_hooks()
    )
    first = await manager.ensure("ENG-1")
    second = await manager.ensure("ENG-1")
    assert first.path == second.path
    assert first.created_now is True
    assert second.created_now is False


@pytest.mark.asyncio
async def test_after_create_failure_rolls_back_directory(tmp_path: Path) -> None:
    hooks = HooksConfig(after_create="exit 7")
    manager = FilesystemWorkspaceManager(
        workspace_root=tmp_path, hooks=hooks, hook_timeout_seconds=5
    )
    with pytest.raises(WorkspaceHookFailedError) as exc:
        await manager.ensure("ENG-2")
    assert exc.value.result.exit_code == 7
    assert not (tmp_path / "ENG-2").exists()


@pytest.mark.asyncio
async def test_run_hook_returns_none_when_unset(tmp_path: Path) -> None:
    manager = FilesystemWorkspaceManager(
        workspace_root=tmp_path, hooks=_empty_hooks()
    )
    ws = await manager.ensure("k")
    result = await manager.run_hook("before_run", ws)
    assert result is None


@pytest.mark.asyncio
async def test_run_hook_before_run_failure_raises(tmp_path: Path) -> None:
    hooks = HooksConfig(before_run="exit 3")
    manager = FilesystemWorkspaceManager(
        workspace_root=tmp_path, hooks=hooks, hook_timeout_seconds=5
    )
    ws = await manager.ensure("k")
    with pytest.raises(WorkspaceHookFailedError):
        await manager.run_hook("before_run", ws)


@pytest.mark.asyncio
async def test_run_hook_after_run_failure_is_swallowed(tmp_path: Path) -> None:
    hooks = HooksConfig(after_run="exit 5")
    manager = FilesystemWorkspaceManager(
        workspace_root=tmp_path, hooks=hooks, hook_timeout_seconds=5
    )
    ws = await manager.ensure("k")
    result = await manager.run_hook("after_run", ws)
    assert result is not None
    assert result.exit_code == 5


@pytest.mark.asyncio
async def test_cleanup_removes_workspace_directory(tmp_path: Path) -> None:
    manager = FilesystemWorkspaceManager(
        workspace_root=tmp_path, hooks=_empty_hooks()
    )
    ws = await manager.ensure("k")
    assert ws.path.exists()
    await manager.cleanup(ws)
    assert not ws.path.exists()


@pytest.mark.asyncio
async def test_cleanup_swallows_before_remove_failure(tmp_path: Path) -> None:
    hooks = HooksConfig(before_remove="exit 1")
    manager = FilesystemWorkspaceManager(
        workspace_root=tmp_path, hooks=hooks, hook_timeout_seconds=5
    )
    ws = await manager.ensure("k")
    await manager.cleanup(ws)
    assert not ws.path.exists()


@pytest.mark.asyncio
async def test_exec_hook_success(tmp_path: Path) -> None:
    result = await exec_hook(
        name="t", script="echo hello && echo world", cwd=tmp_path
    )
    assert result.exit_code == 0
    assert "hello" in result.output
    assert "world" in result.output
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_exec_hook_timeout(tmp_path: Path) -> None:
    with pytest.raises(HookTimeoutError):
        await exec_hook(
            name="slow", script="sleep 5", cwd=tmp_path, timeout_seconds=0.2
        )


@pytest.mark.asyncio
async def test_exec_hook_nonzero_exit(tmp_path: Path) -> None:
    result = await exec_hook(name="fail", script="exit 9", cwd=tmp_path)
    assert result.exit_code == 9
