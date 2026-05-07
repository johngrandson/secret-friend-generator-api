"""GET /runs/{run_id}/detail — fetch run + latest spec + latest plan.

Aggregate read for the operator UI. ``GET /runs/{run_id}`` keeps the
flat run-only payload to preserve backwards compatibility.
"""

from uuid import UUID

from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.plan.serializers import to_plan_output
from src.contexts.symphony.adapters.http.run.deps import GetRunDetailUseCaseDep
from src.contexts.symphony.adapters.http.run.router import router
from src.contexts.symphony.adapters.http.run.serializers import to_run_output
from src.contexts.symphony.adapters.http.spec.serializers import to_spec_output
from src.contexts.symphony.use_cases.run.get_detail import GetRunDetailRequest


@router.get("/{run_id}/detail")
async def get_run_detail(
    run_id: UUID, detail_uc: GetRunDetailUseCaseDep
) -> dict:
    """Return the run with its latest spec and plan in one round-trip."""
    resp = await detail_uc.execute(GetRunDetailRequest(run_id=run_id))
    if not resp.success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=resp.error_message)
    assert resp.run is not None
    return {
        "run": to_run_output(resp.run),
        "latest_spec": to_spec_output(resp.latest_spec) if resp.latest_spec else None,
        "latest_plan": to_plan_output(resp.latest_plan) if resp.latest_plan else None,
        # Phase 09: agent_sessions, gate_results, pull_request — pending repos
        "agent_sessions": [],
        "gate_results": [],
        "pull_request": None,
    }
