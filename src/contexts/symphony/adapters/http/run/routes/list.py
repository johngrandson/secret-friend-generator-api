"""GET /runs/ — list runs with pagination."""

from src.contexts.symphony.adapters.http.run.router import router
from src.contexts.symphony.adapters.http.run.deps import ListRunsUseCaseDep
from src.contexts.symphony.adapters.http.run.serializers import to_run_output
from src.contexts.symphony.use_cases.run.list import ListRunsRequest


@router.get("/")
async def list_runs(
    list_uc: ListRunsUseCaseDep,
    limit: int = 20,
    offset: int = 0,
) -> list:
    resp = await list_uc.execute(ListRunsRequest(limit=limit, offset=offset))
    return [to_run_output(r) for r in resp.runs]
