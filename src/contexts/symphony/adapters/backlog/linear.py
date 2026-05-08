"""Linear GraphQL adapter — issues + comments. Queries live in ./queries/."""

import logging
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from types import TracebackType
from typing import Self, TypeAlias

import httpx

from src.contexts.symphony.adapters.backlog.mapper import normalize_linear_issue
from src.contexts.symphony.domain.backlog.errors import (
    BacklogAuthError,
    BacklogRateLimitError,
    BacklogSchemaError,
    BacklogTransportError,
)
from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.backlog.tracker_config import TrackerConfig

# Opaque GraphQL payload — structure varies by query, validated via isinstance
# guards before consumption. Using `object` instead of `Any` forces explicit
# narrowing and prevents accidental attribute access.
_GraphQLPayload: TypeAlias = dict[str, object]

log = logging.getLogger(__name__)

QUERIES_DIR = Path(__file__).parent / "queries"
PAGE_SIZE = 50
DEFAULT_TIMEOUT_SECONDS = 10.0


def _read_query(name: str) -> str:
    return (QUERIES_DIR / f"{name}.graphql").read_text(encoding="utf-8")


# Loaded once at import; never re-read.
_QUERIES: dict[str, str] = {
    "ActiveIssues": _read_query("active_issues"),
    "IssueByIdentifier": _read_query("issue_by_identifier"),
    "TerminalIssuesSince": _read_query("terminal_issues_since"),
    "CommentCreate": _read_query("comment_create"),
}


class LinearBacklogAdapter:
    """Linear GraphQL implementation of IBacklogAdapter."""

    def __init__(
        self,
        config: TrackerConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if config.kind != "linear":
            raise BacklogSchemaError(
                f"LinearBacklogAdapter requires kind='linear', got {config.kind!r}"
            )
        self._config = config
        self._endpoint = config.endpoint
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": config.api_key,
                "Content-Type": "application/json",
            },
            transport=transport,
            timeout=timeout,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._client.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    def is_terminal(self, state: str) -> bool:
        """Return True if the given state name is a terminal state."""
        return state in self._config.terminal_states

    async def fetch_active_issues(self) -> list[Issue]:
        """Fetch all active issues for the configured project."""
        filt: _GraphQLPayload = {
            "state": {"name": {"in": list(self._config.active_states)}},
            "project": {"slugId": {"eq": self._config.project_slug}},
        }
        return await self._fetch_paginated("ActiveIssues", filt)

    async def fetch_issue(self, identifier: str) -> Issue | None:
        """Fetch a single issue by its human identifier (e.g. ENG-1).

        Returns None if Linear returns null for the issue field.
        """
        data = await self._post("IssueByIdentifier", {"identifier": identifier})
        issue_node = data.get("issue")
        if issue_node is None:
            return None
        if not isinstance(issue_node, dict):
            raise BacklogSchemaError(
                f"Linear issue field is not an object: {issue_node!r}"
            )
        return normalize_linear_issue(issue_node)

    async def post_comment(self, identifier: str, body: str) -> None:
        """Post a Markdown comment on the issue.

        Resolves identifier to Linear's internal UUID via IssueByIdentifier,
        then issues the commentCreate mutation. Two round-trips by design:
        the mutation accepts the UUID, not the human identifier.

        Raises:
            BacklogSchemaError: identifier is unknown or mutation returned
                success=false.
        """
        # Step 1: resolve human identifier → Linear UUID
        lookup_data = await self._post("IssueByIdentifier", {"identifier": identifier})
        issue_node = lookup_data.get("issue")
        if not isinstance(issue_node, dict):
            raise BacklogSchemaError(f"Linear issue not found: {identifier}")
        issue_id = issue_node.get("id")
        if not isinstance(issue_id, str):
            raise BacklogSchemaError(f"Linear issue node missing 'id' for {identifier}")

        # Step 2: post the comment using the UUID
        data = await self._post(
            "CommentCreate",
            {"issueId": issue_id, "body": body},
        )
        result = data.get("commentCreate")
        if not isinstance(result, dict) or not result.get("success"):
            raise BacklogSchemaError(
                f"Linear commentCreate did not succeed for {identifier}: {data!r}"
            )

    async def fetch_terminal_issues_since(self, since: datetime) -> list[Issue]:
        """Fetch issues in terminal states that were updated after `since`."""
        filt: _GraphQLPayload = {
            "state": {"name": {"in": list(self._config.terminal_states)}},
            "updatedAt": {"gt": since.isoformat()},
            "project": {"slugId": {"eq": self._config.project_slug}},
        }
        return await self._fetch_paginated("TerminalIssuesSince", filt)

    async def _fetch_paginated(
        self, query_name: str, filt: _GraphQLPayload
    ) -> list[Issue]:
        issues: list[Issue] = []
        cursor: str | None = None
        while True:
            variables: _GraphQLPayload = {
                "filter": filt,
                "first": PAGE_SIZE,
                "after": cursor,
            }
            data = await self._post(query_name, variables)
            issues_field = data.get("issues")
            if not isinstance(issues_field, dict):
                raise BacklogSchemaError(
                    f"Linear response missing 'issues' object: {data!r}"
                )
            for node in issues_field.get("nodes", []):
                issues.append(normalize_linear_issue(node))
            page_info = issues_field.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                break
            next_cursor = page_info.get("endCursor")
            if not isinstance(next_cursor, str):
                log.warning("Linear hasNextPage=true with no endCursor; stopping")
                break
            cursor = next_cursor
        return issues

    async def _post(self, query_name: str, variables: _GraphQLPayload) -> _GraphQLPayload:
        body = {"query": _QUERIES[query_name], "variables": variables}
        try:
            response = await self._client.post(self._endpoint, json=body)
        except httpx.HTTPError as err:
            raise BacklogTransportError(f"Linear transport error: {err}") from err

        self._raise_for_status(response)

        try:
            payload = response.json()
        except (JSONDecodeError, ValueError) as err:
            raise BacklogSchemaError(f"Linear returned non-JSON: {err}") from err

        errors = payload.get("errors")
        if errors:
            messages = "; ".join(e.get("message", "<no message>") for e in errors)
            raise BacklogSchemaError(f"Linear GraphQL errors: {messages}")

        data = payload.get("data")
        if not isinstance(data, dict):
            raise BacklogSchemaError(
                f"Linear response missing 'data' object: {payload!r}"
            )
        return data

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        if status in (401, 403):
            raise BacklogAuthError(
                f"Linear auth failed ({status}): {response.text[:1000]}"
            )
        if status == 429:
            retry_after_raw = response.headers.get("Retry-After")
            retry_after: float | None = None
            if retry_after_raw:
                try:
                    retry_after = float(retry_after_raw)
                except ValueError:
                    retry_after = None
            raise BacklogRateLimitError(
                f"Linear rate limited: {response.text[:1000]}",
                retry_after_seconds=retry_after,
            )
        if status >= 500:
            raise BacklogTransportError(
                f"Linear server error ({status}): {response.text[:1000]}"
            )
        if status != 200:
            raise BacklogTransportError(
                f"Linear unexpected status {status}: {response.text[:1000]}"
            )
