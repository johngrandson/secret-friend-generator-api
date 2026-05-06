"""ListRunsUseCase — return a paginated list of runs."""

from dataclasses import dataclass, field

from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.use_cases.run.dto import RunDTO


@dataclass
class ListRunsRequest:
    limit: int = 20
    offset: int = 0


@dataclass
class ListRunsResponse:
    runs: list[RunDTO] = field(default_factory=list)
    success: bool = True
    error_message: str | None = None


class ListRunsUseCase:
    def __init__(self, uow: ISymphonyUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, request: ListRunsRequest) -> ListRunsResponse:
        async with self._uow:
            runs = await self._uow.runs.list(
                limit=request.limit, offset=request.offset
            )
        return ListRunsResponse(runs=[RunDTO.from_entity(r) for r in runs])
