# Como Adicionar um Novo Agregado

Receita prática end-to-end. O exemplo usa `Order` como agregado hipotético.
Siga a ordem — cada etapa depende da anterior.

Ao terminar, rode:
```bash
poetry run lint-imports && poetry run pytest && poetry run mypy src && poetry run ruff check src tests
```

---

## 1. Domínio — `src/domain/order/`

### 1.1 Value Objects (se houver)

`src/domain/order/money.py`:
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

`src/domain/order/events.py`:
```python
from dataclasses import dataclass
from uuid import UUID

from src.domain._shared.events import DomainEvent


@dataclass(frozen=True)
class OrderCreated(DomainEvent):
    order_id: UUID
    customer_id: UUID


@dataclass(frozen=True)
class OrderCompleted(DomainEvent):
    order_id: UUID
```

### 1.3 Entidade / Aggregate Root

`src/domain/order/entity.py`:
```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain._shared.aggregate_root import AggregateRoot
from src.domain.order.events import OrderCompleted, OrderCreated
from src.domain.order.money import Money


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

`src/domain/order/repository.py`:
```python
from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from src.domain.order.entity import Order


@runtime_checkable
class IOrderRepository(Protocol):
    async def find_by_id(self, order_id: UUID) -> Optional[Order]: ...
    async def list(self, limit: int = 20, offset: int = 0) -> list[Order]: ...
    async def save(self, order: Order) -> Order: ...
    async def update(self, order: Order) -> Order: ...
    async def delete(self, order_id: UUID) -> bool: ...
```

### 1.5 `__init__.py`

`src/domain/order/__init__.py` — deixe vazio.

---

## 2. Use Cases — `src/use_cases/order/`

Um arquivo por verbo. Exemplo completo para `create`; os demais seguem o mesmo padrão.

Use cases de mutação recebem `event_publisher: IEventPublisher` e publicam após o persist.
Use cases de leitura (`get`, `list`) não precisam de publisher.

`src/use_cases/order/dto.py`:
```python
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.domain.order.entity import Order


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

`src/use_cases/order/create.py`:
```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from src.domain._shared.event_publisher import IEventPublisher
from src.domain.order.entity import Order
from src.domain.order.money import Money
from src.domain.order.repository import IOrderRepository
from src.use_cases.order.dto import OrderDTO


@dataclass
class CreateOrderRequest:
    customer_id: UUID
    total_amount: Decimal


@dataclass
class CreateOrderResponse:
    order: Optional[OrderDTO]
    success: bool
    error_message: Optional[str] = None


class CreateOrderUseCase:
    def __init__(
        self,
        order_repository: IOrderRepository,
        event_publisher: IEventPublisher,
    ) -> None:
        self._repo = order_repository
        self._publisher = event_publisher

    async def execute(self, request: CreateOrderRequest) -> CreateOrderResponse:
        try:
            total = Money(amount=request.total_amount)
            order = Order.create(customer_id=request.customer_id, total=total)
        except ValueError as exc:
            return CreateOrderResponse(None, False, str(exc))
        saved = await self._repo.save(order)
        events = saved.pull_events()
        if events:
            await self._publisher.publish(events)
        return CreateOrderResponse(OrderDTO.from_entity(saved), True)
```

Crie também: `get.py`, `list.py`, `update.py`, `delete.py` — mesma estrutura.
`src/use_cases/order/__init__.py` — deixe vazio.

---

## 3. Driven Adapter — `src/adapters/persistence/order/`

### 3.1 Modelo ORM

`src/adapters/persistence/order/model.py`:
```python
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from src.adapters.persistence.base import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_id: Mapped[UUID] = mapped_column(nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

### 3.2 Mapper

`src/adapters/persistence/order/mapper.py`:
```python
from src.domain.order.entity import Order
from src.domain.order.money import Money
from src.adapters.persistence.order.model import OrderModel


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

### 3.3 Repositório Concreto

`src/adapters/persistence/order/repository.py`:
```python
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.order.entity import Order
from src.adapters.persistence.order.mapper import to_entity, to_model
from src.adapters.persistence.order.model import OrderModel


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
        await self._session.commit()
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
        await self._session.commit()
        await self._session.refresh(model)
        return to_entity(model)

    async def delete(self, order_id: UUID) -> bool:
        cursor = await self._session.execute(
            delete(OrderModel).where(OrderModel.id == order_id)
        )
        await self._session.commit()
        return bool(cursor.rowcount > 0)
```

`src/adapters/persistence/order/__init__.py` — deixe vazio.

---

## 4. Driving Adapter — `src/adapters/http/order/`

### 4.1 Router

`src/adapters/http/order/_router.py`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/orders", tags=["orders"])
```

### 4.2 Schemas (Pydantic — validação de entrada)

`src/adapters/http/order/schemas.py`:
```python
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class CreateOrderInput(BaseModel):
    customer_id: UUID
    total_amount: Decimal
```

### 4.3 Serializers (DTO → dict de saída)

`src/adapters/http/order/serializers.py`:
```python
from src.use_cases.order.dto import OrderDTO


def to_order_output(dto: OrderDTO) -> dict:
    return {
        "id": str(dto.id),
        "customer_id": str(dto.customer_id),
        "total_amount": str(dto.total_amount),
        "currency": dto.currency,
        "is_completed": dto.is_completed,
    }
```

### 4.4 Deps (DI wiring)

`src/adapters/http/order/deps.py`:
```python
from typing import Annotated, Callable

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.events.in_memory_publisher import InMemoryEventPublisher
from src.adapters.persistence.order.repository import SQLAlchemyOrderRepository
from src.infrastructure.container import Container
from src.infrastructure.database import get_session
from src.use_cases.order.create import CreateOrderUseCase

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@inject
def get_create_order_use_case(
    session: SessionDep,
    factory: Callable[..., CreateOrderUseCase] = Depends(
        Provide[Container.create_order_use_case.provider]
    ),
    publisher: InMemoryEventPublisher = Depends(Provide[Container.event_publisher]),
) -> CreateOrderUseCase:
    return factory(
        order_repository=SQLAlchemyOrderRepository(session),
        event_publisher=publisher,
    )


CreateOrderUseCaseDep = Annotated[CreateOrderUseCase, Depends(get_create_order_use_case)]
```

### 4.5 Routes

`src/adapters/http/order/routes/create.py`:
```python
from fastapi import HTTPException, status

from src.adapters.http.order._router import router
from src.adapters.http.order.deps import CreateOrderUseCaseDep
from src.adapters.http.order.schemas import CreateOrderInput
from src.adapters.http.order.serializers import to_order_output
from src.use_cases.order.create import CreateOrderRequest


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(data: CreateOrderInput, create_uc: CreateOrderUseCaseDep) -> dict:
    resp = await create_uc.execute(
        CreateOrderRequest(customer_id=data.customer_id, total_amount=data.total_amount)
    )
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    return to_order_output(resp.order)
```

`src/adapters/http/order/__init__.py` — vazio.

---

## 5. Container DI — `src/infrastructure/container.py`

Adicione ao `Container` (após os providers de `user`):

```python
from src.adapters.persistence.order.repository import SQLAlchemyOrderRepository
from src.use_cases.order.create import CreateOrderUseCase

# dentro da classe Container:
order_repository = providers.Factory(SQLAlchemyOrderRepository)
create_order_use_case = providers.Factory(
    CreateOrderUseCase,
    order_repository=order_repository,
    event_publisher=event_publisher,   # Singleton já existente
)
```

Adicione o módulo de deps ao `wiring_config`:
```python
wiring_config = containers.WiringConfiguration(
    modules=[
        "src.adapters.http.user.deps",
        "src.adapters.http.order.deps",   # <-- adicionar
    ],
)
```

---

## 6. Main — `src/main.py`

```python
from src.adapters.http.order._router import router as order_router
from src.adapters.http.order.routes import create  # noqa: F401 — registra a rota

app.include_router(order_router)
```

---

## 7. Migration Alembic

```bash
poetry run alembic revision --autogenerate -m "add orders table"
poetry run alembic upgrade head
```

---

## 8. Testes

Espelhe a estrutura de `tests/unit/` e `tests/integration/` usada para `user`:

```
tests/
├── unit/
│   ├── domain/order/
│   │   ├── __init__.py
│   │   ├── test_money.py          # invariantes de Money
│   │   └── test_order_entity.py   # Order.create() coleta OrderCreated, complete() coleta OrderCompleted
│   └── use_cases/order/
│       ├── __init__.py
│       └── test_create_order.py   # AsyncMock do repositório e do publisher
└── integration/
    └── order/
        ├── __init__.py
        ├── test_order_repository.py   # contra SQLite in-memory
        └── test_order_endpoints.py    # HTTP via httpx AsyncClient
```

---

## 9. Checklist Final

```
[ ] src/domain/order/{__init__,entity,repository,events}.py criados
[ ] src/domain/order/money.py (value object) criado
[ ] src/use_cases/order/{__init__,dto,create,get,list,update,delete}.py criados
[ ] src/adapters/persistence/order/{__init__,model,mapper,repository}.py criados
[ ] src/adapters/http/order/{__init__,_router,schemas,serializers,deps}.py criados
[ ] src/adapters/http/order/routes/{__init__,create,...}.py criados
[ ] Container: providers de order_repository e use cases adicionados (event_publisher já existe)
[ ] Container: wiring_config.modules atualizado
[ ] main.py: include_router(order_router)
[ ] Alembic migration gerada e aplicada
[ ] Testes escritos (unit + integration) — incluindo asserção de eventos coletados
[ ] poetry run lint-imports   → "Contracts: N kept, 0 broken"
[ ] poetry run pytest         → todos os testes passam
[ ] poetry run mypy src       → clean
[ ] poetry run ruff check src tests → clean
```
