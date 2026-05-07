"""Unit tests for write_mcp_config."""

import json
from pathlib import Path

import pytest

from src.infrastructure.adapters.agent_runner.claude_code import (
    MCP_CONFIG_FILENAME,
    MCPConfigEmptyError,
    MCPConfigError,
    write_mcp_config,
)
from src.infrastructure.adapters.workflow import MCPServerConfig


def test_write_mcp_config_writes_expected_payload(tmp_path: Path) -> None:
    servers = {
        "linear": MCPServerConfig(
            command="npx",
            args=["@linear/mcp-server"],
            env={"LINEAR_API_KEY": "secret"},
        )
    }
    path = write_mcp_config(workspace=tmp_path, servers=servers)
    assert path == tmp_path / MCP_CONFIG_FILENAME

    payload = json.loads(path.read_text("utf-8"))
    assert payload == {
        "mcpServers": {
            "linear": {
                "command": "npx",
                "args": ["@linear/mcp-server"],
                "env": {"LINEAR_API_KEY": "secret"},
            }
        }
    }


def test_write_mcp_config_omits_empty_args_and_env(tmp_path: Path) -> None:
    servers = {"plain": MCPServerConfig(command="bin")}
    path = write_mcp_config(workspace=tmp_path, servers=servers)
    payload = json.loads(path.read_text("utf-8"))
    assert payload == {"mcpServers": {"plain": {"command": "bin"}}}


def test_write_mcp_config_empty_servers_raises(tmp_path: Path) -> None:
    with pytest.raises(MCPConfigEmptyError):
        write_mcp_config(workspace=tmp_path, servers={})


def test_write_mcp_config_missing_workspace_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(MCPConfigError):
        write_mcp_config(
            workspace=missing,
            servers={"x": MCPServerConfig(command="y")},
        )
