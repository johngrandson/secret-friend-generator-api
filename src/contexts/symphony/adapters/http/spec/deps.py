"""FastAPI dependency aliases for the Spec HTTP layer.

All wiring lives in
:mod:`src.contexts.symphony.adapters.http.use_case_deps`; this module
just binds the typed ``Annotated[..., Depends(...)]`` aliases the route
handlers import.
"""

from typing import Annotated

from dependency_injector.wiring import Provide
from fastapi import Depends

from src.contexts.symphony.adapters.http.use_case_deps import make_use_case_dep
from src.contexts.symphony.use_cases.spec.approve import ApproveSpecUseCase
from src.contexts.symphony.use_cases.spec.create import CreateSpecUseCase
from src.contexts.symphony.use_cases.spec.get import GetSpecUseCase
from src.contexts.symphony.use_cases.spec.list_for_run import ListSpecsForRunUseCase
from src.contexts.symphony.use_cases.spec.reject import RejectSpecUseCase
from src.infrastructure.containers import Container

get_create_spec_use_case = make_use_case_dep(
    Provide[Container.symphony.create_spec_use_case.provider],
    with_publisher=True,
)
get_get_spec_use_case = make_use_case_dep(
    Provide[Container.symphony.get_spec_use_case.provider],
    with_publisher=False,
)
get_list_specs_for_run_use_case = make_use_case_dep(
    Provide[Container.symphony.list_specs_for_run_use_case.provider],
    with_publisher=False,
)
get_approve_spec_use_case = make_use_case_dep(
    Provide[Container.symphony.approve_spec_use_case.provider],
    with_publisher=True,
)
get_reject_spec_use_case = make_use_case_dep(
    Provide[Container.symphony.reject_spec_use_case.provider],
    with_publisher=True,
)


CreateSpecUseCaseDep = Annotated[CreateSpecUseCase, Depends(get_create_spec_use_case)]
GetSpecUseCaseDep = Annotated[GetSpecUseCase, Depends(get_get_spec_use_case)]
ListSpecsForRunUseCaseDep = Annotated[
    ListSpecsForRunUseCase, Depends(get_list_specs_for_run_use_case)
]
ApproveSpecUseCaseDep = Annotated[
    ApproveSpecUseCase, Depends(get_approve_spec_use_case)
]
RejectSpecUseCaseDep = Annotated[RejectSpecUseCase, Depends(get_reject_spec_use_case)]
