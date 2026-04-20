"""Tests for agents app registry / dependency helpers."""

import pytest
from fastapi import HTTPException

import src.api.agents.dependencies as deps


@pytest.fixture(autouse=True)
def reset_registry():
    """Isolate each test: clear module-level state before and after."""
    deps._apps.clear()
    deps._mcp_tools.clear()
    deps._mcp_client = None
    yield
    deps._apps.clear()
    deps._mcp_tools.clear()
    deps._mcp_client = None


# --- get_app ---


def test_get_app_raises_404_when_empty():
    with pytest.raises(HTTPException) as exc_info:
        deps.get_app("supervisor")
    assert exc_info.value.status_code == 404


def test_get_app_detail_mentions_app_name():
    with pytest.raises(HTTPException) as exc_info:
        deps.get_app("supervisor")
    assert "supervisor" in exc_info.value.detail


def test_get_app_detail_says_none_available_when_empty():
    with pytest.raises(HTTPException) as exc_info:
        deps.get_app("supervisor")
    assert "none" in exc_info.value.detail


def test_get_app_detail_lists_available_when_populated():
    deps._apps["supervisor"] = object()
    with pytest.raises(HTTPException) as exc_info:
        deps.get_app("unknown")
    assert "supervisor" in exc_info.value.detail


def test_get_app_returns_registered_app():
    sentinel = object()
    deps._apps["supervisor"] = sentinel
    result = deps.get_app("supervisor")
    assert result is sentinel


def test_get_app_raises_404_for_unregistered_when_others_exist():
    deps._apps["supervisor"] = object()
    with pytest.raises(HTTPException) as exc_info:
        deps.get_app("swarm")
    assert exc_info.value.status_code == 404


# --- get_app_names ---


def test_get_app_names_empty():
    assert deps.get_app_names() == []


def test_get_app_names_returns_registered_names():
    deps._apps["supervisor"] = object()
    deps._apps["swarm"] = object()
    names = deps.get_app_names()
    assert set(names) == {"supervisor", "swarm"}


# --- get_mcp_tools_count ---


def test_get_mcp_tools_count_zero_when_empty():
    assert deps.get_mcp_tools_count() == 0


def test_get_mcp_tools_count_reflects_loaded_tools():
    deps._mcp_tools.extend(["tool_a", "tool_b", "tool_c"])
    assert deps.get_mcp_tools_count() == 3
