"""Integration tests for LinearBacklogAdapter using httpx.MockTransport."""

import json
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from src.contexts.symphony.adapters.backlog.config import TrackerConfig
from src.contexts.symphony.adapters.backlog.linear import LinearBacklogAdapter
from src.contexts.symphony.adapters.backlog.mapper import normalize_linear_issue
from src.contexts.symphony.domain.backlog.errors import (
    BacklogAuthError,
    BacklogRateLimitError,
    BacklogSchemaError,
    BacklogTransportError,
)
from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _full_issue_node(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "00000000-0000-0000-0000-000000000001",
        "identifier": "ENG-1",
        "title": "Sample issue",
        "description": "A sample description.",
        "priority": 2,
        "state": {"name": "In Progress"},
        "branchName": "eng-1-sample",
        "url": "https://linear.app/x/issue/ENG-1",
        "labels": {"nodes": [{"name": "bug"}]},
        "inverseRelations": {
            "nodes": [{"type": "blocks", "issue": {"identifier": "ENG-99"}}]
        },
        "createdAt": "2025-01-01T00:00:00.000Z",
        "updatedAt": "2025-01-02T00:00:00.000Z",
    }
    base.update(overrides)
    return base


def _make_adapter(transport: httpx.MockTransport) -> LinearBacklogAdapter:
    config = TrackerConfig(api_key="lin_api_test", project_slug="ai-platform")
    return LinearBacklogAdapter(config, transport=transport)


def _paginated_response(
    nodes: list[dict[str, Any]], *, has_next: bool = False, cursor: str = "cursor-end"
) -> dict[str, Any]:
    return {
        "data": {
            "issues": {
                "pageInfo": {
                    "hasNextPage": has_next,
                    "endCursor": cursor if has_next else None,
                },
                "nodes": nodes,
            }
        }
    }


def _single_issue_response(issue: dict[str, Any] | None) -> dict[str, Any]:
    return {"data": {"issue": issue}}


# ---------------------------------------------------------------------------
# normalize_linear_issue unit tests
# ---------------------------------------------------------------------------


class TestNormalizeLinearIssue:
    def test_full_payload_maps_all_fields(self) -> None:
        node = _full_issue_node()
        issue = normalize_linear_issue(node)

        assert isinstance(issue, Issue)
        assert issue.identifier == "ENG-1"
        assert issue.title == "Sample issue"
        assert issue.description == "A sample description."
        assert issue.priority is IssuePriority.HIGH
        assert issue.state == "In Progress"
        assert issue.branch_name == "eng-1-sample"
        assert issue.url == "https://linear.app/x/issue/ENG-1"
        assert issue.labels == ("bug",)
        assert issue.blocked_by == ("ENG-99",)
        assert issue.created_at == datetime(2025, 1, 1, tzinfo=UTC)
        assert issue.updated_at == datetime(2025, 1, 2, tzinfo=UTC)

    def test_none_description_defaults_to_empty_string(self) -> None:
        node = _full_issue_node(description=None)
        issue = normalize_linear_issue(node)
        assert issue.description == ""

    def test_missing_labels_defaults_to_empty_tuple(self) -> None:
        node = _full_issue_node()
        del node["labels"]
        issue = normalize_linear_issue(node)
        assert issue.labels == ()

    def test_missing_inverse_relations_defaults_to_empty_blocked_by(self) -> None:
        node = _full_issue_node()
        del node["inverseRelations"]
        issue = normalize_linear_issue(node)
        assert issue.blocked_by == ()

    def test_non_blocks_inverse_relations_excluded(self) -> None:
        node = _full_issue_node(
            inverseRelations={
                "nodes": [
                    {"type": "duplicate", "issue": {"identifier": "ENG-5"}},
                    {"type": "blocks", "issue": {"identifier": "ENG-10"}},
                ]
            }
        )
        issue = normalize_linear_issue(node)
        assert issue.blocked_by == ("ENG-10",)


# ---------------------------------------------------------------------------
# fetch_active_issues
# ---------------------------------------------------------------------------


class TestFetchActiveIssues:
    @pytest.mark.asyncio
    async def test_normalizes_full_payload(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_paginated_response([_full_issue_node()]))

        adapter = _make_adapter(httpx.MockTransport(handler))
        issues = await adapter.fetch_active_issues()

        assert len(issues) == 1
        assert issues[0].identifier == "ENG-1"
        assert issues[0].priority is IssuePriority.HIGH
        assert issues[0].labels == ("bug",)

    @pytest.mark.asyncio
    async def test_sends_correct_filter_and_auth_header(self) -> None:
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["headers"] = dict(request.headers)
            captured["payload"] = json.loads(request.content)
            return httpx.Response(200, json=_paginated_response([]))

        adapter = _make_adapter(httpx.MockTransport(handler))
        await adapter.fetch_active_issues()

        assert captured["headers"]["authorization"] == "lin_api_test"
        filt = captured["payload"]["variables"]["filter"]
        assert filt["state"]["name"]["in"] == ["Todo", "In Progress"]
        assert filt["project"]["slug"]["eq"] == "ai-platform"

    @pytest.mark.asyncio
    async def test_paginates_until_no_next(self) -> None:
        calls: list[dict[str, Any]] = []
        page_1 = _full_issue_node(identifier="ENG-1")
        page_2 = _full_issue_node(identifier="ENG-2")

        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            calls.append(payload)
            after = payload["variables"].get("after")
            if after is None:
                return httpx.Response(
                    200, json=_paginated_response([page_1], has_next=True)
                )
            assert after == "cursor-end"
            return httpx.Response(200, json=_paginated_response([page_2]))

        adapter = _make_adapter(httpx.MockTransport(handler))
        issues = await adapter.fetch_active_issues()

        assert [i.identifier for i in issues] == ["ENG-1", "ENG-2"]
        assert len(calls) == 2


# ---------------------------------------------------------------------------
# fetch_issue
# ---------------------------------------------------------------------------


class TestFetchIssue:
    @pytest.mark.asyncio
    async def test_returns_none_when_missing(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_single_issue_response(None))

        adapter = _make_adapter(httpx.MockTransport(handler))
        result = await adapter.fetch_issue("ENG-999")

        assert result is None

    @pytest.mark.asyncio
    async def test_normalizes_when_present(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            assert payload["variables"]["identifier"] == "ENG-1"
            return httpx.Response(
                200, json=_single_issue_response(_full_issue_node())
            )

        adapter = _make_adapter(httpx.MockTransport(handler))
        issue = await adapter.fetch_issue("ENG-1")

        assert issue is not None
        assert issue.identifier == "ENG-1"
        assert issue.title == "Sample issue"


# ---------------------------------------------------------------------------
# post_comment
# ---------------------------------------------------------------------------


class TestPostComment:
    @pytest.mark.asyncio
    async def test_two_step_flow(self) -> None:
        captured: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            captured.append(payload)
            if "IssueByIdentifier" in payload["query"]:
                return httpx.Response(
                    200, json=_single_issue_response(_full_issue_node())
                )
            return httpx.Response(
                200,
                json={
                    "data": {
                        "commentCreate": {
                            "success": True,
                            "comment": {"id": "cmt-1"},
                        }
                    }
                },
            )

        adapter = _make_adapter(httpx.MockTransport(handler))
        await adapter.post_comment("ENG-1", "hello world")

        assert len(captured) == 2
        assert "IssueByIdentifier" in captured[0]["query"]
        assert "CommentCreate" in captured[1]["query"]
        assert captured[1]["variables"]["issueId"] == "00000000-0000-0000-0000-000000000001"
        assert captured[1]["variables"]["body"] == "hello world"

    @pytest.mark.asyncio
    async def test_raises_when_create_fails(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            if "IssueByIdentifier" in payload["query"]:
                return httpx.Response(
                    200, json=_single_issue_response(_full_issue_node())
                )
            return httpx.Response(
                200,
                json={"data": {"commentCreate": {"success": False}}},
            )

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogSchemaError, match="did not succeed"):
            await adapter.post_comment("ENG-1", "body")

    @pytest.mark.asyncio
    async def test_raises_when_issue_not_found(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_single_issue_response(None))

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogSchemaError, match="not found"):
            await adapter.post_comment("ENG-999", "body")


# ---------------------------------------------------------------------------
# HTTP error mapping
# ---------------------------------------------------------------------------


class TestHttpErrorMapping:
    @pytest.mark.asyncio
    async def test_401_raises_auth_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, text="unauthorized")

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogAuthError):
            await adapter.fetch_active_issues()

    @pytest.mark.asyncio
    async def test_403_raises_auth_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, text="forbidden")

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogAuthError):
            await adapter.fetch_active_issues()

    @pytest.mark.asyncio
    async def test_429_raises_rate_limit_error_with_retry_after(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, headers={"Retry-After": "30"}, text="slow down")

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogRateLimitError) as exc_info:
            await adapter.fetch_active_issues()

        assert exc_info.value.retry_after_seconds == 30.0

    @pytest.mark.asyncio
    async def test_429_without_retry_after_has_none(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, text="slow down")

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogRateLimitError) as exc_info:
            await adapter.fetch_active_issues()

        assert exc_info.value.retry_after_seconds is None

    @pytest.mark.asyncio
    async def test_500_raises_transport_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, text="bad gateway")

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogTransportError):
            await adapter.fetch_active_issues()

    @pytest.mark.asyncio
    async def test_network_error_raises_transport_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogTransportError):
            await adapter.fetch_active_issues()


# ---------------------------------------------------------------------------
# Schema / payload error handling
# ---------------------------------------------------------------------------


class TestSchemaErrors:
    @pytest.mark.asyncio
    async def test_malformed_json_raises_schema_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"<html>not json</html>")

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogSchemaError, match="non-JSON"):
            await adapter.fetch_active_issues()

    @pytest.mark.asyncio
    async def test_graphql_errors_array_raises_schema_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "errors": [{"message": "Invalid filter"}]
                },
            )

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogSchemaError, match="Invalid filter"):
            await adapter.fetch_active_issues()

    @pytest.mark.asyncio
    async def test_missing_data_field_raises_schema_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"data": None})

        adapter = _make_adapter(httpx.MockTransport(handler))
        with pytest.raises(BacklogSchemaError):
            await adapter.fetch_active_issues()

    def test_unknown_priority_raises_schema_error(self) -> None:
        node = _full_issue_node(priority=99)
        with pytest.raises(BacklogSchemaError, match="priority"):
            normalize_linear_issue(node)

    def test_missing_state_raises_schema_error(self) -> None:
        node = _full_issue_node()
        node["state"] = None
        with pytest.raises(BacklogSchemaError):
            normalize_linear_issue(node)

    def test_missing_required_field_raises_schema_error(self) -> None:
        node = _full_issue_node()
        del node["identifier"]
        with pytest.raises(BacklogSchemaError, match="identifier"):
            normalize_linear_issue(node)


# ---------------------------------------------------------------------------
# is_terminal
# ---------------------------------------------------------------------------


class TestIsTerminal:
    def test_matches_configured_terminal_states(self) -> None:
        config = TrackerConfig(api_key="k", project_slug="p")
        adapter = LinearBacklogAdapter(
            config, transport=httpx.MockTransport(lambda r: httpx.Response(200))
        )
        assert adapter.is_terminal("Done") is True
        assert adapter.is_terminal("Cancelled") is True
        assert adapter.is_terminal("Canceled") is True
        assert adapter.is_terminal("Duplicate") is True
        assert adapter.is_terminal("Closed") is True
        assert adapter.is_terminal("Todo") is False
        assert adapter.is_terminal("In Progress") is False

    def test_custom_terminal_states_override_defaults(self) -> None:
        config = TrackerConfig(
            api_key="k",
            project_slug="p",
            terminal_states=("Shipped",),
        )
        adapter = LinearBacklogAdapter(
            config, transport=httpx.MockTransport(lambda r: httpx.Response(200))
        )
        assert adapter.is_terminal("Shipped") is True
        assert adapter.is_terminal("Done") is False


# ---------------------------------------------------------------------------
# Async context manager
# ---------------------------------------------------------------------------


class TestAsyncContextManager:
    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=_paginated_response([]))

        async with LinearBacklogAdapter(
            TrackerConfig(api_key="k", project_slug="p"),
            transport=httpx.MockTransport(handler),
        ) as adapter:
            issues = await adapter.fetch_active_issues()
            assert issues == []

    @pytest.mark.asyncio
    async def test_aclose_does_not_raise(self) -> None:
        adapter = _make_adapter(
            httpx.MockTransport(lambda r: httpx.Response(200, json=_paginated_response([])))
        )
        await adapter.aclose()


# ---------------------------------------------------------------------------
# fetch_terminal_issues_since
# ---------------------------------------------------------------------------


class TestFetchTerminalIssuesSince:
    @pytest.mark.asyncio
    async def test_sends_correct_terminal_filter(self) -> None:
        captured: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["payload"] = json.loads(request.content)
            return httpx.Response(200, json=_paginated_response([_full_issue_node()]))

        adapter = _make_adapter(httpx.MockTransport(handler))
        since = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)
        issues = await adapter.fetch_terminal_issues_since(since)

        assert len(issues) == 1
        filt = captured["payload"]["variables"]["filter"]
        assert set(filt["state"]["name"]["in"]) == {
            "Done", "Cancelled", "Canceled", "Duplicate", "Closed"
        }
        assert filt["updatedAt"]["gt"] == since.isoformat()
        assert filt["project"]["slug"]["eq"] == "ai-platform"
