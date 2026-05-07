"""GitHubCodeHost — ``ICodeHost`` impl backed by ``gh`` CLI + raw ``git push``.

Each method spawns a subprocess via the injected ``runner``, captures
stdout/stderr/exit code, and converts well-known ``gh`` payloads
(JSON for queries; the URL line for ``gh pr create``) into the typed
return values defined by the ``ICodeHost`` port. Tests inject scripted
runners that emit canned ``SubprocessResult`` values without touching
the OS.
"""

import json
import logging
from collections.abc import Sequence
from pathlib import Path

from src.contexts.symphony.adapters.code_host.github.gh_cli import (
    SubprocessRunner,
    default_subprocess_runner,
)
from src.contexts.symphony.domain.code_host import (
    CodeHostCommandError,
    CreatedPR,
    ExistingPR,
)

log = logging.getLogger(__name__)


class GitHubCodeHost:
    """``ICodeHost`` backed by the GitHub ``gh`` CLI + ``git push``.

    Satisfies the Protocol structurally (no inheritance). The four
    operations match the orchestrator's open-or-update PR flow.
    """

    def __init__(self, *, runner: SubprocessRunner | None = None) -> None:
        self._runner = runner or default_subprocess_runner

    async def push_branch(self, *, branch: str, workspace: Path) -> None:
        result = await self._runner(
            ["git", "push", "-u", "origin", branch], workspace, None
        )
        if result.exit_code != 0:
            raise CodeHostCommandError(
                f"git push failed for branch {branch!r}",
                exit_code=result.exit_code,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"),
            )

    async def find_pr_for_branch(
        self, *, branch: str, workspace: Path
    ) -> ExistingPR | None:
        argv = [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--json",
            "number,url,isDraft",
        ]
        result = await self._runner(argv, workspace, None)
        if result.exit_code != 0:
            raise CodeHostCommandError(
                f"gh pr list failed for branch {branch!r}",
                exit_code=result.exit_code,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"),
            )

        try:
            items = json.loads(result.stdout or b"[]")
        except json.JSONDecodeError as err:
            raise CodeHostCommandError(
                f"gh pr list returned non-JSON: {err}",
                exit_code=0,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"),
            ) from err

        if not isinstance(items, list) or not items:
            return None

        first = items[0]
        return ExistingPR(
            number=int(first["number"]),
            url=str(first["url"]),
            is_draft=bool(first.get("isDraft", False)),
        )

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
        argv: list[str] = [
            "gh",
            "pr",
            "create",
            "--base",
            base,
            "--head",
            branch,
            "--title",
            title,
            "--body-file",
            "-",
        ]
        if draft:
            argv.append("--draft")
        for label in labels:
            argv.extend(["--label", label])

        result = await self._runner(argv, workspace, body.encode("utf-8"))
        if result.exit_code != 0:
            raise CodeHostCommandError(
                f"gh pr create failed for branch {branch!r}",
                exit_code=result.exit_code,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"),
            )

        stdout = result.stdout.decode("utf-8", errors="replace")
        url = stdout.strip().splitlines()[-1] if stdout else ""
        if not url:
            raise CodeHostCommandError(
                "gh pr create succeeded but emitted no URL",
                exit_code=0,
                stdout=stdout,
                stderr=result.stderr.decode("utf-8", errors="replace"),
            )

        number = parse_pr_number_from_url(url)
        if number == 0:
            raise CodeHostCommandError(
                f"gh pr create emitted unparseable URL: {url!r}",
                exit_code=0,
                stdout=stdout,
                stderr=result.stderr.decode("utf-8", errors="replace"),
            )
        return CreatedPR(number=number, url=url)

    async def update_pr(
        self, *, pr_number: int, title: str, body: str, workspace: Path
    ) -> None:
        argv = [
            "gh",
            "pr",
            "edit",
            str(pr_number),
            "--title",
            title,
            "--body-file",
            "-",
        ]
        result = await self._runner(argv, workspace, body.encode("utf-8"))
        if result.exit_code != 0:
            raise CodeHostCommandError(
                f"gh pr edit failed for PR #{pr_number}",
                exit_code=result.exit_code,
                stdout=result.stdout.decode("utf-8", errors="replace"),
                stderr=result.stderr.decode("utf-8", errors="replace"),
            )


def parse_pr_number_from_url(url: str) -> int:
    """Extract ``42`` from ``https://github.com/owner/repo/pull/42``.

    Falls back to 0 if the URL is malformed; callers should treat 0 as
    a sign that the PR exists but its number is unrecoverable from the
    ``gh`` output.
    """
    parts = url.rstrip("/").split("/")
    if len(parts) < 2:
        return 0
    try:
        return int(parts[-1])
    except ValueError:
        return 0
