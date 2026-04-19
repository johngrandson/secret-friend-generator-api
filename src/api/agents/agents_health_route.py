"""GET /health endpoint for the agents API."""

from fastapi import APIRouter

from src.api.agents.agents_dependencies import get_app_names, get_mcp_tools_count
from src.api.agents.agents_schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service status, registered app names and MCP tool count."""
    return HealthResponse(
        status="ok",
        apps=get_app_names(),
        mcp_tools_loaded=get_mcp_tools_count(),
    )
