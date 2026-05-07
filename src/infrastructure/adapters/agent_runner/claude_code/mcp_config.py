"""MCP config materialization — writes ``<workspace>/.mcp.json``.

Takes the operator's declared ``mcp_servers`` map from the parsed
WORKFLOW.md, renders it into the JSON shape Claude Code's
``--mcp-config`` flag expects, and drops it inside the per-issue
workspace. The runner picks up the path through
``ClaudeCodeConfig.mcp_config_path``.

No explicit cleanup function: workspace cleanup ``rm -rf``s the whole
directory, taking ``.mcp.json`` with it.
"""

import json
import logging
from pathlib import Path

from src.infrastructure.adapters.workflow import MCPServerConfig

log = logging.getLogger(__name__)

MCP_CONFIG_FILENAME = ".mcp.json"


class MCPConfigError(Exception):
    """Base error for MCP config materialization failures."""


class MCPConfigEmptyError(MCPConfigError):
    """``write_mcp_config`` was called with zero servers."""


def write_mcp_config(
    *, workspace: Path, servers: dict[str, MCPServerConfig]
) -> Path:
    """Serialize ``servers`` into ``<workspace>/.mcp.json`` and return the path.

    Raises:
        MCPConfigEmptyError: ``servers`` is empty.
        MCPConfigError: workspace is missing or unwritable.
    """
    if not servers:
        raise MCPConfigEmptyError(
            "write_mcp_config called with no servers; skip the call instead"
        )
    if not workspace.is_dir():
        raise MCPConfigError(f"workspace does not exist: {workspace}")

    payload = {"mcpServers": {name: _server_dict(s) for name, s in servers.items()}}
    path = workspace / MCP_CONFIG_FILENAME
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as err:
        raise MCPConfigError(f"failed to write {path}: {err}") from err

    log.info(
        "mcp_config_written path=%s servers=%s",
        path,
        sorted(servers.keys()),
    )
    return path


def _server_dict(server: MCPServerConfig) -> dict[str, object]:
    out: dict[str, object] = {"command": server.command}
    if server.args:
        out["args"] = list(server.args)
    if server.env:
        out["env"] = dict(server.env)
    return out
