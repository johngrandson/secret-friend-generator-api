"""GET /runs/{run_id} — fetch a single run by id."""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.run.router import router
from src.contexts.symphony.adapters.http.run.deps import GetRunUseCaseDep
from src.contexts.symphony.adapters.http.run.serializers import to_run_output
from src.contexts.symphony.use_cases.run.get import GetRunRequest


@router.get("/{run_id}")
async def get_run(run_id: UUID, get_uc: GetRunUseCaseDep) -> dict:
    resp = await get_uc.execute(GetRunRequest(run_id=run_id))
    if not resp.success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
    assert resp.run is not None
    return to_run_output(resp.run)
