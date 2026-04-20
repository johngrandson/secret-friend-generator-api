"""Tests for the MCP tools loader."""

import pytest

import src.domain.agents.tools.mcp_tools as mod


@pytest.fixture(autouse=True)
def reset_cache() -> None:
    """Reset module-level cache between tests."""
    mod._cached = None
    yield
    mod._cached = None


@pytest.mark.asyncio
async def test_load_mcp_tools_no_path_returns_empty() -> None:
    result = await mod.load_mcp_tools(config_path=None)
    assert result["tools"] == []
    assert result["client"] is None


@pytest.mark.asyncio
async def test_load_mcp_tools_missing_file_returns_empty() -> None:
    result = await mod.load_mcp_tools(config_path="/tmp/nonexistent-mcp-config.json")
    assert result["tools"] == []
    assert result["client"] is None


@pytest.mark.asyncio
async def test_load_mcp_tools_empty_string_path_returns_empty() -> None:
    result = await mod.load_mcp_tools(config_path="")
    assert result["tools"] == []
    assert result["client"] is None


def test_get_mcp_tools_before_load_returns_empty_list() -> None:
    assert mod.get_mcp_tools() == []
