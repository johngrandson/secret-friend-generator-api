"""FastAPI dependency aliases for the Run HTTP layer.

All wiring lives in
:mod:`src.contexts.symphony.adapters.http.use_case_deps`; this module
just binds the typed ``Annotated[..., Depends(...)]`` aliases the route
handlers import.
"""

from typing import Annotated

from dependency_injector.wiring import Provide
from fastapi import Depends

from src.contexts.symphony.adapters.http.use_case_deps import make_use_case_dep
from src.contexts.symphony.use_cases.run.create import CreateRunUseCase
from src.contexts.symphony.use_cases.run.get import GetRunUseCase
from src.contexts.symphony.use_cases.run.list import ListRunsUseCase
from src.infrastructure.containers import Container

get_create_run_use_case = make_use_case_dep(
    Provide[Container.symphony.create_run_use_case.provider],
    with_publisher=True,
)
get_get_run_use_case = make_use_case_dep(
    Provide[Container.symphony.get_run_use_case.provider],
    with_publisher=False,
)
get_list_runs_use_case = make_use_case_dep(
    Provide[Container.symphony.list_runs_use_case.provider],
    with_publisher=False,
)


CreateRunUseCaseDep = Annotated[CreateRunUseCase, Depends(get_create_run_use_case)]
GetRunUseCaseDep = Annotated[GetRunUseCase, Depends(get_get_run_use_case)]
ListRunsUseCaseDep = Annotated[ListRunsUseCase, Depends(get_list_runs_use_case)]
