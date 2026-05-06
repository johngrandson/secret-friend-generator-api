"""ListSpecsForRunUseCase — return all spec versions for a given run."""

from dataclasses import dataclass, field
from uuid import UUID

from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.spec.dto import SpecDTO


@dataclass
class ListSpecsForRunRequest:
    run_id: UUID


@dataclass
class ListSpecsForRunResponse:
    specs: list[SpecDTO] = field(default_factory=list)
    success: bool = True
    error_message: str | None = None


class ListSpecsForRunUseCase:
    def __init__(self, uow: ISymphonyUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: ListSpecsForRunRequest) -> ListSpecsForRunResponse:
        async with self._uow:
            specs = await self._uow.specs.list_by_run(request.run_id)
        return ListSpecsForRunResponse(specs=[SpecDTO.from_entity(s) for s in specs])
