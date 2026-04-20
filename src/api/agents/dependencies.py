"""App registry and lifecycle helpers for the agents API."""

import logging
from typing import Any

from fastapi import HTTPException

log = logging.getLogger(__name__)

_apps: dict[str, Any] = {}
_mcp_tools: list = []
_mcp_client: Any = None


def get_app(app_name: str) -> Any:
    """Return the compiled graph for *app_name* or raise HTTP 404."""
    if app_name not in _apps:
        available = ", ".join(_apps.keys()) if _apps else "none"
        raise HTTPException(
            status_code=404,
            detail=f'Unknown app: "{app_name}". Available: {available}',
        )
    return _apps[app_name]


def get_app_names() -> list[str]:
    """Return names of all registered apps."""
    return list(_apps.keys())


def get_mcp_tools_count() -> int:
    """Return number of loaded MCP tools."""
    return len(_mcp_tools)


async def init_agents_registry() -> None:
    """Load MCP tools and build all agent apps. Called at startup."""
    global _apps, _mcp_tools, _mcp_client

    from src.domain.agents.tools.mcp import load_mcp_tools
    from src.shared.app_config import settings

    mcp_result = await load_mcp_tools(settings.MCP_SERVERS_PATH or None)
    _mcp_tools = mcp_result["tools"]
    _mcp_client = mcp_result["client"]

    from src.domain.agents.apps.analyst import create_analyst_app
    from src.domain.agents.apps.interrupt import create_interrupt_app
    from src.domain.agents.apps.rag import create_rag_app, init_rag_store
    from src.domain.agents.apps.researcher import create_researcher_app
    from src.domain.agents.apps.supervisor import create_supervisor_app
    from src.domain.agents.apps.support import create_support_app
    from src.domain.agents.apps.swarm import create_swarm_app

    rag_store = await init_rag_store()
    _apps.update(
        {
            "supervisor": create_supervisor_app(_mcp_tools),
            "swarm": create_swarm_app(_mcp_tools),
            "interrupt": create_interrupt_app(),
            "analyst": create_analyst_app(),
            "researcher": create_researcher_app(),
            "rag": create_rag_app(rag_store),
            "support": create_support_app(),
        }
    )
    log.info("Agents registry initialised with apps: %s", list(_apps.keys()))


async def shutdown_agents() -> None:
    """Close the MCP client connection gracefully."""
    global _mcp_client
    if _mcp_client:
        try:
            await _mcp_client.close()
        except Exception as exc:
            log.warning("MCP client close failed: %s", exc)
        _mcp_client = None
