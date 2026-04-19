"""MCP tools loader — loads and caches tools from a MultiServerMCPClient config."""

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)
_cached: dict[str, Any] | None = None


async def load_mcp_tools(config_path: str | None = None) -> dict[str, Any]:
    """Load MCP tools from a JSON config file, caching the result.

    Args:
        config_path: Path to the MCP server config JSON. If None or the file
            does not exist, an empty result is returned immediately.

    Returns:
        Dict with keys ``tools`` (list) and ``client`` (MultiServerMCPClient or None).

    Raises:
        RuntimeError: If the config file exists but cannot be parsed.
    """
    global _cached
    if _cached is not None:
        return _cached

    empty: dict[str, Any] = {"tools": [], "client": None}

    if not config_path or not Path(config_path).exists():
        return empty

    try:
        raw = json.loads(Path(config_path).read_text())
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"Failed to parse MCP config at {config_path}: {e}") from e

    if not isinstance(raw, dict) or not raw:
        return empty

    from langchain_mcp_adapters.client import MultiServerMCPClient  # noqa: PLC0415

    client = MultiServerMCPClient(raw)
    tools = await client.get_tools()
    _cached = {"tools": tools, "client": client}
    return _cached


def get_mcp_tools() -> list:
    """Return the cached list of MCP tools (empty list if not yet loaded).

    Returns:
        List of loaded MCP tool objects.
    """
    return _cached["tools"] if _cached else []
