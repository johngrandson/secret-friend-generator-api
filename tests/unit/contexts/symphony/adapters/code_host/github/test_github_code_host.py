"""Unit tests for GitHubCodeHost with scripted SubprocessRunner.

The runner stub captures argv/cwd/stdin per call so each test can
assert exactly what flags reached the ``gh`` CLI without spawning a
real process.
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.contexts.symphony.adapters.code_host.github import (
    GitHubCodeHost,
    SubprocessResult,
)
from src.contexts.symphony.adapters.code_host.github.adapter import (
    parse_pr_number_from_url,
)
from src.contexts.symphony.domain.code_host import CodeHostCommandError


@dataclass
class _Call:
    argv: list[str]
    cwd: Path
    stdin: bytes | None


class _ScriptedRunner:
    """A SubprocessRunner that returns canned results in order, tracking calls."""

    def __init__(self, results: list[SubprocessResult]) -> None:
        self._queue = list(results)
        self.calls: list[_Call] = []

    async def __call__(
        self, argv: Sequence[str], cwd: Path, stdin: bytes | None
    ) -> SubprocessResult:
        self.calls.append(_Call(argv=list(argv), cwd=cwd, stdin=stdin))
        if not self._queue:
            raise AssertionError("ScriptedRunner ran out of canned results")
        return self._queue.pop(0)


def _ok(stdout: bytes = b"", stderr: bytes = b"") -> SubprocessResult:
    return SubprocessResult(exit_code=0, stdout=stdout, stderr=stderr)


def _fail(stdout: bytes = b"", stderr: bytes = b"err") -> SubprocessResult:
    return SubprocessResult(exit_code=1, stdout=stdout, stderr=stderr)


@pytest.mark.asyncio
async def test_push_branch_calls_git_with_expected_args(tmp_path: Path) -> None:
    runner = _ScriptedRunner([_ok()])
    host = GitHubCodeHost(runner=runner)

    await host.push_branch(branch="feat/x", workspace=tmp_path)

    assert runner.calls[0].argv == ["git", "push", "-u", "origin", "feat/x"]
    assert runner.calls[0].cwd == tmp_path
    assert runner.calls[0].stdin is None


@pytest.mark.asyncio
async def test_push_branch_raises_on_nonzero_exit(tmp_path: Path) -> None:
    runner = _ScriptedRunner([_fail(stderr=b"auth denied")])
    host = GitHubCodeHost(runner=runner)

    with pytest.raises(CodeHostCommandError) as exc:
        await host.push_branch(branch="feat/x", workspace=tmp_path)
    assert exc.value.exit_code == 1
    assert "auth denied" in exc.value.stderr


@pytest.mark.asyncio
async def test_find_pr_for_branch_returns_existing_pr(tmp_path: Path) -> None:
    payload = json.dumps(
        [{"number": 42, "url": "https://x/pr/42", "isDraft": True}]
    ).encode("utf-8")
    runner = _ScriptedRunner([_ok(stdout=payload)])
    host = GitHubCodeHost(runner=runner)

    pr = await host.find_pr_for_branch(branch="feat/x", workspace=tmp_path)

    assert pr is not None
    assert pr.number == 42
    assert pr.url == "https://x/pr/42"
    assert pr.is_draft is True
    assert "--head" in runner.calls[0].argv
    assert "feat/x" in runner.calls[0].argv


@pytest.mark.asyncio
async def test_find_pr_for_branch_returns_none_on_empty_list(
    tmp_path: Path,
) -> None:
    runner = _ScriptedRunner([_ok(stdout=b"[]")])
    host = GitHubCodeHost(runner=runner)

    pr = await host.find_pr_for_branch(branch="feat/x", workspace=tmp_path)

    assert pr is None


@pytest.mark.asyncio
async def test_find_pr_for_branch_raises_on_non_json(tmp_path: Path) -> None:
    runner = _ScriptedRunner([_ok(stdout=b"not json")])
    host = GitHubCodeHost(runner=runner)

    with pytest.raises(CodeHostCommandError, match="non-JSON"):
        await host.find_pr_for_branch(branch="feat/x", workspace=tmp_path)


@pytest.mark.asyncio
async def test_create_pr_passes_body_via_stdin_and_extracts_url(
    tmp_path: Path,
) -> None:
    runner = _ScriptedRunner(
        [_ok(stdout=b"https://github.com/x/y/pull/7\n")]
    )
    host = GitHubCodeHost(runner=runner)

    pr = await host.create_pr(
        branch="feat/x",
        base="main",
        title="t",
        body="some **markdown** body",
        labels=("agent", "automation"),
        draft=True,
        workspace=tmp_path,
    )

    assert pr.number == 7
    assert pr.url == "https://github.com/x/y/pull/7"
    call = runner.calls[0]
    assert call.argv[0:3] == ["gh", "pr", "create"]
    assert "--body-file" in call.argv and "-" in call.argv
    assert "--draft" in call.argv
    assert call.argv.count("--label") == 2
    assert call.stdin == b"some **markdown** body"


@pytest.mark.asyncio
async def test_create_pr_raises_when_no_url_emitted(tmp_path: Path) -> None:
    runner = _ScriptedRunner([_ok(stdout=b"")])
    host = GitHubCodeHost(runner=runner)

    with pytest.raises(CodeHostCommandError, match="no URL"):
        await host.create_pr(
            branch="feat/x",
            base="main",
            title="t",
            body="b",
            labels=(),
            draft=False,
            workspace=tmp_path,
        )


@pytest.mark.asyncio
async def test_create_pr_propagates_failure(tmp_path: Path) -> None:
    runner = _ScriptedRunner([_fail(stderr=b"protected branch")])
    host = GitHubCodeHost(runner=runner)

    with pytest.raises(CodeHostCommandError):
        await host.create_pr(
            branch="feat/x",
            base="main",
            title="t",
            body="b",
            labels=(),
            draft=False,
            workspace=tmp_path,
        )


@pytest.mark.asyncio
async def test_update_pr_passes_body_via_stdin(tmp_path: Path) -> None:
    runner = _ScriptedRunner([_ok()])
    host = GitHubCodeHost(runner=runner)

    await host.update_pr(
        pr_number=11, title="new title", body="updated", workspace=tmp_path
    )

    call = runner.calls[0]
    assert call.argv == [
        "gh",
        "pr",
        "edit",
        "11",
        "--title",
        "new title",
        "--body-file",
        "-",
    ]
    assert call.stdin == b"updated"


@pytest.mark.asyncio
async def test_update_pr_raises_on_failure(tmp_path: Path) -> None:
    runner = _ScriptedRunner([_fail()])
    host = GitHubCodeHost(runner=runner)

    with pytest.raises(CodeHostCommandError):
        await host.update_pr(
            pr_number=1, title="t", body="b", workspace=tmp_path
        )


def test_parse_pr_number_from_url_handles_normal_url() -> None:
    assert parse_pr_number_from_url("https://github.com/x/y/pull/42") == 42


def test_parse_pr_number_from_url_strips_trailing_slash() -> None:
    assert parse_pr_number_from_url("https://github.com/x/y/pull/13/") == 13


def test_parse_pr_number_from_url_returns_zero_when_unparseable() -> None:
    assert parse_pr_number_from_url("not-a-url") == 0
    assert parse_pr_number_from_url("https://github.com/x/y/pull/abc") == 0
