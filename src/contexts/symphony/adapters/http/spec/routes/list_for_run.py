"""GET /specs/ — list all spec versions for a given run."""

from uuid import UUID

from fastapi import Query

from src.contexts.symphony.adapters.http.spec.router import router
from src.contexts.symphony.adapters.http.spec.deps import ListSpecsForRunUseCaseDep
from src.contexts.symphony.adapters.http.spec.serializers import to_spec_output
from src.contexts.symphony.use_cases.spec.list_for_run import ListSpecsForRunRequest


@router.get("/")
async def list_specs_for_run(
    list_uc: ListSpecsForRunUseCaseDep,
    run_id: UUID = Query(...),
) -> list:
    resp = await list_uc.execute(ListSpecsForRunRequest(run_id=run_id))
    return [to_spec_output(s) for s in resp.specs]
