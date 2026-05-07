"""GET /runs/{run_id}/spec — return the latest spec for a run.

Convenience shortcut over ``GET /specs/?run_id=`` returning only the
highest-version spec instead of the full version history.
"""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.spec.deps import (
    ListSpecsForRunUseCaseDep,
)
from src.contexts.symphony.adapters.http.spec.serializers import to_spec_output
from src.contexts.symphony.adapters.http.run.router import router
from src.contexts.symphony.use_cases.spec.list_for_run import (
    ListSpecsForRunRequest,
)


@router.get("/{run_id}/spec")
async def get_latest_spec_for_run(
    run_id: UUID, list_uc: ListSpecsForRunUseCaseDep
) -> dict:
    resp = await list_uc.execute(ListSpecsForRunRequest(run_id=run_id))
    if not resp.specs:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="No spec found for this run."
        )
    latest = max(resp.specs, key=lambda s: s.version)
    return to_spec_output(latest)
