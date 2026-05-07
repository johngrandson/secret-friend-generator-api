# Como Adicionar um Novo Agregado

Receita prática end-to-end. O exemplo usa `Order` como agregado hipotético
dentro do contexto `symphony`.

Antes de começar: **qual bounded context recebe o agregado?**

- Se o agregado pertence a `identity` (ex: `Role`, `Permission`) → substitua
  `symphony` por `identity` em todos os paths abaixo.
- Se não pertence a nenhum contexto existente → leia primeiro
  [how-to-add-bounded-context.md](./how-to-add-bounded-context.md) e crie o
  contexto antes de seguir esta receita.

Ver [architecture.md](./architecture.md) para as regras de camadas e dependências.

Siga a ordem — cada etapa depende da anterior.

> **Reuso de bases**: se o agregado segue um padrão já existente
> (write-once approval, p.ex.), prefira herdar de uma base do contexto
> em vez de reimplementar o ciclo de vida. Ex.: `Spec` e `Plan` em
> `symphony` herdam de
> `src/contexts/symphony/domain/approval/aggregate.ApprovedAggregate`,
> sobrescrevem apenas os hooks `_make_approved_event` /
> `_make_rejected_event` / `_make_created_event` e ficam em ~45 linhas.
> Antes de implementar `approve` / `reject` do zero, verifique se já
> existe uma base reutilizável. Validações repetidas (ex.: "campo não
> pode ser branco") vão para `domain/validators.py` (`ensure_non_blank`).

Ao terminar, rode os gates de verificação:

```bash
poetry run lint-imports && poetry run pytest && poetry run mypy src && poetry run ruff check src tests
```

> **Imports**: o projeto proíbe imports relativos (ruff rule `TID252`). Use sempre
> caminhos absolutos: `from src.contexts.symphony.domain.order.entity import Order`.

---

## 1. Domínio — `src/contexts/symphony/domain/order/`

### 1.1 Value Objects (se houver)

`src/contexts/symphony/domain/order/money.py`:

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "BRL"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount must be non-negative.")
```

### 1.2 Eventos de Domínio

`src/contexts/symphony/domain/order/events.py`:

```python
from dataclasses import dataclass
from uuid import UUID

from src.shared.events import DomainEvent


@dataclass(frozen=True)
class OrderCreated(DomainEvent):
    order_id: UUID
    customer_id: UUID


@dataclass(frozen=True)
class OrderCompleted(DomainEvent):
    order_id: UUID
```

### 1.3 Entidade / Aggregate Root

`src/contexts/symphony/domain/order/entity.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.shared.aggregate_root import AggregateRoot
from src.contexts.symphony.domain.order.events import OrderCompleted, OrderCreated
from src.contexts.symphony.domain.order.money import Money


@dataclass
class Order(AggregateRoot):
    total: Money
    customer_id: UUID
    id: UUID = field(default_factory=uuid4)
    is_completed: bool = False
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def complete(self) -> None:
        if self.is_completed:
            raise ValueError("Order is already completed.")
        self.is_completed = True
        self.collect_event(OrderCompleted(order_id=self.id))

    @classmethod
    def create(cls, customer_id: UUID, total: Money) -> "Order":
        if total.amount <= 0:
            raise ValueError("Order total must be positive.")
        order = cls(total=total, customer_id=customer_id)
        order.collect_event(OrderCreated(order_id=order.id, customer_id=customer_id))
        return order
```

### 1.4 Output Port (Protocol)

`src/contexts/symphony/domain/order/repository.py`:

```python
from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from src.contexts.symphony.domain.order.entity import Order


@runtime_checkable
class IOrderRepository(Protocol):
    async def find_by_id(self, order_id: UUID) -> Optional[Order]: ...
    async def list(self, limit: int = 20, offset: int = 0) -> list[Order]: ...
    async def save(self, order: Order) -> Order: ...
    async def update(self, order: Order) -> Order: ...
    async def delete(self, order_id: UUID) -> bool: ...
```

### 1.5 `__init__.py`

`src/contexts/symphony/domain/order/__init__.py` — deixe vazio.

---

## 2. Atualizar o UoW Protocol do contexto

Adicione o novo repositório ao Protocol em
`src/contexts/symphony/domain/unit_of_work.py`:

```python
if TYPE_CHECKING:
    from src.contexts.symphony.domain.run.repository import IRunRepository
    from src.contexts.symphony.domain.spec.repository import ISpecRepository
    from src.contexts.symphony.domain.plan.repository import IPlanRepository
    from src.contexts.symphony.domain.order.repository import IOrderRepository  # NEW


@runtime_checkable
class ISymphonyUnitOfWork(Protocol):
    runs: "IRunRepository"
    specs: "ISpecRepository"
    plans: "IPlanRepository"
    orders: "IOrderRepository"  # NEW
    ...
```

---

## 3. Use Cases — `src/contexts/symphony/use_cases/order/`

Um arquivo por verbo. Exemplo completo para `create`; os demais seguem o mesmo padrão.

Use cases de mutação recebem `uow: ISymphonyUnitOfWork` e `event_publisher`.
Use cases de leitura (`get`, `list`) recebem apenas `uow`.

`src/contexts/symphony/use_cases/order/dto.py`:

```python
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.contexts.symphony.domain.order.entity import Order


@dataclass(frozen=True)
class OrderDTO:
    id: UUID
    customer_id: UUID
    total_amount: Decimal
    currency: str
    is_completed: bool

    @classmethod
    def from_entity(cls, order: Order) -> "OrderDTO":
        return cls(
            id=order.id,
            customer_id=order.customer_id,
            total_amount=order.total.amount,
            currency=order.total.currency,
            is_completed=order.is_completed,
        )
```

`src/contexts/symphony/use_cases/order/create.py`:

```python
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.shared.event_publisher import IEventPublisher
from src.contexts.symphony.domain.unit_of_work import ISymphonyUnitOfWork
from src.contexts.symphony.domain.order.entity import Order
from src.contexts.symphony.domain.order.money import Money
from src.contexts.symphony.use_cases.order.dto import OrderDTO


@dataclass
class CreateOrderRequest:
    customer_id: UUID
    total_amount: Decimal


@dataclass
class CreateOrderResponse:
    order: OrderDTO | None
    success: bool
    error_message: str | None = None


class CreateOrderUseCase:
    def __init__(
        self,
        uow: ISymphonyUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: CreateOrderRequest) -> CreateOrderResponse:
        try:
            total = Money(amount=request.total_amount)
            order = Order.create(customer_id=request.customer_id, total=total)
        except ValueError as exc:
            return CreateOrderResponse(None, False, str(exc))

        async with self._uow:
            saved = await self._uow.orders.save(order)  # flush, sem commit
            await self._uow.commit()                     # transação confirmada
            events = order.pull_events()                 # do aggregate de entrada

        if events:
            await self._publisher.publish(events)        # após commit
        return CreateOrderResponse(OrderDTO.from_entity(saved), True)
```

> **Regra crítica:** `order.pull_events()` — **nunca** `saved.pull_events()`.
> O mapper retorna uma instância nova de `Order` sem eventos. Ver
> [event-publication-pattern.md](./event-publication-pattern.md).

> **Repositórios usam `flush()`, não `commit()`**: o UoW é o único dono da
> transação. Se um repositório chamar `session.commit()` diretamente, quebrará
> o contrato do UoW.

Crie também: `get.py`, `list.py`, `update.py`, `delete.py` — mesma estrutura.
`src/contexts/symphony/use_cases/order/__init__.py` — deixe vazio.

---

## 4. Driven Adapter — `src/contexts/symphony/adapters/persistence/order/`

### 4.1 Modelo ORM

`src/contexts/symphony/adapters/persistence/order/model.py`:

```python
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.adapters.persistence.base import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_id: Mapped[UUID] = mapped_column(nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

### 4.2 Mapper

`src/contexts/symphony/adapters/persistence/order/mapper.py`:

```python
from src.contexts.symphony.domain.order.entity import Order
from src.contexts.symphony.domain.order.money import Money
from src.contexts.symphony.adapters.persistence.order.model import OrderModel


def to_entity(model: OrderModel) -> Order:
    return Order(
        id=model.id,
        customer_id=model.customer_id,
        total=Money(amount=model.total_amount, currency=model.currency),
        is_completed=model.is_completed,
        created_at=model.created_at,
    )


def to_model(order: Order) -> OrderModel:
    return OrderModel(
        id=order.id,
        customer_id=order.customer_id,
        total_amount=order.total.amount,
        currency=order.total.currency,
        is_completed=order.is_completed,
        created_at=order.created_at,
    )
```

### 4.3 Repositório Concreto

`src/contexts/symphony/adapters/persistence/order/repository.py`:

```python
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.symphony.domain.order.entity import Order
from src.contexts.symphony.adapters.persistence.order.mapper import to_entity, to_model
from src.contexts.symphony.adapters.persistence.order.model import OrderModel


class SQLAlchemyOrderRepository:
    """Implements IOrderRepository structurally (no explicit inheritance)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, order_id: UUID) -> Optional[Order]:
        result = await self._session.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )
        row = result.scalar_one_or_none()
        return to_entity(row) if row else None

    async def list(self, limit: int = 20, offset: int = 0) -> list[Order]:
        result = await self._session.execute(
            select(OrderModel).order_by(OrderModel.created_at).limit(limit).offset(offset)
        )
        return [to_entity(row) for row in result.scalars().all()]

    async def save(self, order: Order) -> Order:
        model = to_model(order)
        self._session.add(model)
        await self._session.flush()        # sem commit — UoW comita
        await self._session.refresh(model)
        return to_entity(model)

    async def update(self, order: Order) -> Order:
        result = await self._session.execute(
            select(OrderModel).where(OrderModel.id == order.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Order {order.id} not found for update.")
        model.is_completed = order.is_completed
        await self._session.flush()        # sem commit — UoW comita
        await self._session.refresh(model)
        return to_entity(model)

    async def delete(self, order_id: UUID) -> bool:
        cursor = await self._session.execute(
            delete(OrderModel).where(OrderModel.id == order_id)
        )
        await self._session.flush()        # sem commit — UoW comita
        return bool(cursor.rowcount > 0)
```

`src/contexts/symphony/adapters/persistence/order/__init__.py` — deixe vazio.

### 4.4 Atualizar o UoW Adapter

Adicione o novo repositório em
`src/contexts/symphony/adapters/persistence/unit_of_work.py`:

```python
from src.contexts.symphony.adapters.persistence.order.repository import (
    SQLAlchemyOrderRepository,
)


class SQLAlchemySymphonyUnitOfWork:
    runs: SQLAlchemyRunRepository
    specs: SQLAlchemySpecRepository
    plans: SQLAlchemyPlanRepository
    orders: SQLAlchemyOrderRepository  # NEW

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.runs = SQLAlchemyRunRepository(session)
        self.specs = SQLAlchemySpecRepository(session)
        self.plans = SQLAlchemyPlanRepository(session)
        self.orders = SQLAlchemyOrderRepository(session)  # NEW
    ...
```

### 4.5 Registrar o modelo no registry

`src/infrastructure/adapters/persistence/registry.py` — adicione uma linha:

```python
import src.contexts.symphony.adapters.persistence.order.model  # noqa: F401 — registers OrderModel
```

---

## 5. Driving Adapter — `src/contexts/symphony/adapters/http/order/`

### 5.1 Router

`src/contexts/symphony/adapters/http/order/router.py`:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/orders", tags=["orders"])
```

### 5.2 Schemas (Pydantic — validação de entrada)

`src/contexts/symphony/adapters/http/order/schemas.py`:

```python
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CreateOrderInput(BaseModel):
    customer_id: UUID
    total_amount: Decimal
```

### 5.3 Serializers (DTO → dict de saída)

`src/contexts/symphony/adapters/http/order/serializers.py`:

```python
from src.contexts.symphony.use_cases.order.dto import OrderDTO


def to_order_output(dto: OrderDTO) -> dict:
    return {
        "id": str(dto.id),
        "customer_id": str(dto.customer_id),
        "total_amount": str(dto.total_amount),
        "currency": dto.currency,
        "is_completed": dto.is_completed,
    }
```

### 5.4 Deps (DI wiring)

`src/contexts/symphony/adapters/http/order/deps.py`:

```python
from typing import Annotated
from collections.abc import Callable

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.adapters.events.in_memory_publisher import InMemoryEventPublisher
from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.infrastructure.containers import Container
from src.infrastructure.database import get_session
from src.contexts.symphony.use_cases.order.create import CreateOrderUseCase

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@inject
def get_create_order_use_case(
    session: SessionDep,
    factory: Callable[..., CreateOrderUseCase] = Depends(
        Provide[Container.symphony.create_order_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(Provide[Container.core.event_publisher]),
) -> CreateOrderUseCase:
    return factory(
        uow=SQLAlchemySymphonyUnitOfWork(session),
        event_publisher=publisher,
    )


CreateOrderUseCaseDep = Annotated[CreateOrderUseCase, Depends(get_create_order_use_case)]
```

### 5.5 Routes

`src/contexts/symphony/adapters/http/order/routes/create.py`:

```python
from fastapi import HTTPException, status

from src.contexts.symphony.adapters.http.order.router import router
from src.contexts.symphony.adapters.http.order.deps import CreateOrderUseCaseDep
from src.contexts.symphony.adapters.http.order.schemas import CreateOrderInput
from src.contexts.symphony.adapters.http.order.serializers import to_order_output
from src.contexts.symphony.use_cases.order.create import CreateOrderRequest


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(data: CreateOrderInput, create_uc: CreateOrderUseCaseDep) -> dict:
    resp = await create_uc.execute(
        CreateOrderRequest(customer_id=data.customer_id, total_amount=data.total_amount)
    )
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.order is not None
    return to_order_output(resp.order)
```

### 5.6 Package `__init__.py`

`src/contexts/symphony/adapters/http/order/__init__.py`:

```python
"""Order HTTP adapter package."""

from src.contexts.symphony.adapters.http.order.router import router
import src.contexts.symphony.adapters.http.order.routes  # noqa: F401 — triggers route registration

__all__ = ["router"]
```

`src/contexts/symphony/adapters/http/order/routes/__init__.py` — deixe vazio.

---

## 6. Container DI — `src/infrastructure/containers/symphony.py`

Adicione os providers do novo agregado ao `SymphonyContainer`:

```python
from src.contexts.symphony.use_cases.order.create import CreateOrderUseCase

class SymphonyContainer(containers.DeclarativeContainer):
    ...
    # --- Order ---
    create_order_use_case = providers.Factory(
        CreateOrderUseCase,
        uow=symphony_uow,
        event_publisher=event_publisher,
    )
    # adicione get_order_use_case, list_orders_use_case, etc. da mesma forma
```

O `symphony_uow` já existe e a nova instância `SQLAlchemySymphonyUnitOfWork`
já expõe `orders` após a atualização do passo 4.4 — nenhuma mudança adicional
no UoW factory é necessária.

---

## 7. Main — `src/main.py`

```python
from src.contexts.symphony.adapters.http.order import router as order_router

# dentro de create_app():
app.include_router(order_router)
```

Adicione também `"src.contexts.symphony.adapters.http"` ao `wiring_config` em
`src/infrastructure/containers/root.py` se o pacote symphony ainda não estiver lá:

```python
wiring_config = containers.WiringConfiguration(
    packages=[
        "src.contexts.identity.adapters.http",
        "src.contexts.symphony.adapters.http",  # adicione se ainda não existir
    ],
)
```

---

## 8. Migration Alembic

```bash
poetry run alembic revision --autogenerate -m "add orders table"
poetry run alembic upgrade head
```

---

## 9. Testes

Espelhe a estrutura usada para `identity` e `symphony`:

```
tests/
├── unit/
│   └── contexts/
│       └── symphony/
│           ├── domain/
│           │   └── order/
│           │       ├── __init__.py
│           │       ├── test_money.py          # invariantes de Money
│           │       └── test_order_entity.py   # Order.create() coleta OrderCreated
│           └── use_cases/
│               └── order/
│                   ├── __init__.py
│                   └── test_create_order.py   # FakeSymphonyUoW + AsyncMock publisher
└── integration/
    └── contexts/
        └── symphony/
            └── order/
                ├── __init__.py
                ├── test_repository.py         # contra SQLite in-memory
                └── test_event_publication.py  # via UoW real + FakePublisher
```

### Padrão de unit test com FakeSymphonyUoW

`FakeSymphonyUoW` (em `tests/conftest.py`) já expõe `runs`, `specs` e `plans`
como `AsyncMock`. Após adicionar `orders` ao UoW real (passo 2 e 4.4), adicione
`orders` também ao `FakeSymphonyUoW`:

```python
class FakeSymphonyUoW:
    def __init__(self) -> None:
        self.runs = AsyncMock()
        self.specs = AsyncMock()
        self.plans = AsyncMock()
        self.orders = AsyncMock()  # NEW
        self.committed = False
        self.rolled_back = False
    ...
```

Exemplo de unit test:

```python
from tests.conftest import FakeSymphonyUoW

async def test_create_order_success(uow, publisher):
    uow.orders.save.return_value = Order.create(
        customer_id=uuid4(), total=Money(Decimal("100.00"))
    )

    resp = await CreateOrderUseCase(uow=uow, event_publisher=publisher).execute(
        CreateOrderRequest(customer_id=uuid4(), total_amount=Decimal("100.00"))
    )

    assert resp.success is True
    assert uow.committed is True
    publisher.publish.assert_called_once()
```

---

## 10. Checklist Final

```
[ ] src/contexts/symphony/domain/order/__init__.py criado (vazio)
[ ] src/contexts/symphony/domain/order/entity.py criado
[ ] src/contexts/symphony/domain/order/events.py criado
[ ] src/contexts/symphony/domain/order/repository.py criado
[ ] src/contexts/symphony/domain/order/money.py criado (se houver VO)
[ ] src/contexts/symphony/domain/unit_of_work.py: orders adicionado ao Protocol
[ ] src/contexts/symphony/use_cases/order/__init__.py criado (vazio)
[ ] src/contexts/symphony/use_cases/order/dto.py criado
[ ] src/contexts/symphony/use_cases/order/create.py criado
[ ] src/contexts/symphony/use_cases/order/{get,list,update,delete}.py criados
[ ] src/contexts/symphony/adapters/persistence/order/__init__.py criado (vazio)
[ ] src/contexts/symphony/adapters/persistence/order/model.py criado
[ ] src/contexts/symphony/adapters/persistence/order/mapper.py criado
[ ] src/contexts/symphony/adapters/persistence/order/repository.py criado
[ ] src/contexts/symphony/adapters/persistence/unit_of_work.py: orders adicionado
[ ] src/infrastructure/adapters/persistence/registry.py: import de order.model adicionado
[ ] src/contexts/symphony/adapters/http/order/ criado com router, schemas, serializers, deps
[ ] src/contexts/symphony/adapters/http/order/routes/create.py criado
[ ] src/infrastructure/containers/symphony.py: create_order_use_case adicionado
[ ] src/infrastructure/containers/root.py: wiring_config inclui symphony adapters http
[ ] src/main.py: include_router(order_router)
[ ] Alembic migration gerada e aplicada
[ ] tests/conftest.py: FakeSymphonyUoW.orders adicionado
[ ] Testes unit escritos (domain + use case) — incluindo asserção de eventos
[ ] Testes integration escritos (repository + event publication)
[ ] poetry run lint-imports   -> "Contracts: N kept, 0 broken"
[ ] poetry run pytest         -> todos os testes passam
[ ] poetry run mypy src       -> clean
[ ] poetry run ruff check src tests -> clean
```
