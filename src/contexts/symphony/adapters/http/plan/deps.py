"""FastAPI dependency aliases for the Plan HTTP layer.

All wiring lives in
:mod:`src.contexts.symphony.adapters.http.use_case_deps`; this module
just binds the typed ``Annotated[..., Depends(...)]`` aliases the route
handlers import.
"""

from typing import Annotated

from dependency_injector.wiring import Provide
from fastapi import Depends

from src.contexts.symphony.adapters.http.use_case_deps import make_use_case_dep
from src.contexts.symphony.use_cases.plan.approve import ApprovePlanUseCase
from src.contexts.symphony.use_cases.plan.create import CreatePlanUseCase
from src.contexts.symphony.use_cases.plan.get import GetPlanUseCase
from src.contexts.symphony.use_cases.plan.list_for_run import ListPlansForRunUseCase
from src.contexts.symphony.use_cases.plan.reject import RejectPlanUseCase
from src.infrastructure.containers import Container

get_create_plan_use_case = make_use_case_dep(
    Provide[Container.symphony.create_plan_use_case.provider],
    with_publisher=True,
)
get_get_plan_use_case = make_use_case_dep(
    Provide[Container.symphony.get_plan_use_case.provider],
    with_publisher=False,
)
get_list_plans_for_run_use_case = make_use_case_dep(
    Provide[Container.symphony.list_plans_for_run_use_case.provider],
    with_publisher=False,
)
get_approve_plan_use_case = make_use_case_dep(
    Provide[Container.symphony.approve_plan_use_case.provider],
    with_publisher=True,
)
get_reject_plan_use_case = make_use_case_dep(
    Provide[Container.symphony.reject_plan_use_case.provider],
    with_publisher=True,
)


CreatePlanUseCaseDep = Annotated[CreatePlanUseCase, Depends(get_create_plan_use_case)]
GetPlanUseCaseDep = Annotated[GetPlanUseCase, Depends(get_get_plan_use_case)]
ListPlansForRunUseCaseDep = Annotated[
    ListPlansForRunUseCase, Depends(get_list_plans_for_run_use_case)
]
ApprovePlanUseCaseDep = Annotated[
    ApprovePlanUseCase, Depends(get_approve_plan_use_case)
]
RejectPlanUseCaseDep = Annotated[RejectPlanUseCase, Depends(get_reject_plan_use_case)]
