# Como Adicionar um Novo Bounded Context

Receita prática para criar um contexto novo do zero (ex: `billing`, `analytics`).
O exemplo usa `billing` como nome hipotético.

Ver [architecture.md](./architecture.md) para a explicação de por que contextos
são isolados e como o `.importlinter` aplica essa separação.

Ao terminar, rode os gates de verificação:

```bash
poetry run lint-imports && poetry run pytest && poetry run mypy src && poetry run ruff check src tests
```

---

## 1. Estrutura de diretórios

Crie os pacotes vazios:

```bash
mkdir -p src/contexts/billing/domain
mkdir -p src/contexts/billing/use_cases
mkdir -p src/contexts/billing/adapters/http
mkdir -p src/contexts/billing/adapters/persistence
```

Crie os `__init__.py` vazios:

```bash
touch src/contexts/billing/__init__.py
touch src/contexts/billing/domain/__init__.py
touch src/contexts/billing/use_cases/__init__.py
touch src/contexts/billing/adapters/__init__.py
touch src/contexts/billing/adapters/http/__init__.py
touch src/contexts/billing/adapters/persistence/__init__.py
```

Espelhe a estrutura de `src/contexts/identity/`:

```
src/contexts/billing/
├── __init__.py
├── domain/
│   ├── __init__.py
│   └── unit_of_work.py      # IBillingUnitOfWork Protocol (passo 2)
├── use_cases/
│   └── __init__.py
└── adapters/
    ├── __init__.py
    ├── http/
    │   └── __init__.py
    └── persistence/
        ├── __init__.py
        └── unit_of_work.py  # SQLAlchemyBillingUnitOfWork (passo 3)
```

Espelhe também a estrutura de testes:

```bash
mkdir -p tests/unit/contexts/billing/domain
mkdir -p tests/unit/contexts/billing/use_cases
mkdir -p tests/integration/contexts/billing
touch tests/unit/contexts/billing/__init__.py
touch tests/unit/contexts/billing/domain/__init__.py
touch tests/unit/contexts/billing/use_cases/__init__.py
touch tests/integration/contexts/billing/__init__.py
```

---

## 2. UoW Protocol no domínio

`src/contexts/billing/domain/unit_of_work.py`:

```python
"""IBillingUnitOfWork — output port for atomic billing context transactions."""

from types import TracebackType
from typing import Protocol, runtime_checkable


@runtime_checkable
class IBillingUnitOfWork(Protocol):
    """Transactional boundary for the billing bounded context.

    Usage::

        async with uow:
            ...
            await uow.commit()
    """

    # Adicione atributos de repositório conforme os agregados forem criados:
    # invoices: "IInvoiceRepository"

    async def __aenter__(self) -> "IBillingUnitOfWork": ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
```

O Protocol começa sem atributos de repositório — eles são adicionados à medida
que os agregados do contexto são criados (seguindo
[how-to-add-aggregate.md](./how-to-add-aggregate.md)).

---

## 3. UoW Adapter na persistência

`src/contexts/billing/adapters/persistence/unit_of_work.py`:

```python
"""SQLAlchemyBillingUnitOfWork — adapter implementing IBillingUnitOfWork."""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyBillingUnitOfWork:
    """SQLAlchemy-backed unit of work for the billing bounded context."""

    # Adicione atributos de repositório conforme os agregados forem criados:
    # invoices: SQLAlchemyInvoiceRepository

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        # self.invoices = SQLAlchemyInvoiceRepository(session)

    async def __aenter__(self) -> "SQLAlchemyBillingUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
```

---

## 4. Container DI do novo contexto

`src/infrastructure/containers/billing.py`:

```python
"""Billing context container — UoW + use case providers."""

from dependency_injector import containers, providers

from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)
from src.contexts.billing.adapters.persistence.unit_of_work import (
    SQLAlchemyBillingUnitOfWork,
)


class BillingContainer(containers.DeclarativeContainer):
    event_publisher: providers.Dependency[InMemoryEventPublisher] = (
        providers.Dependency()
    )

    billing_uow = providers.Factory(SQLAlchemyBillingUnitOfWork)

    # Adicione use case factories conforme forem criados:
    # create_invoice_use_case = providers.Factory(
    #     CreateInvoiceUseCase,
    #     uow=billing_uow,
    #     event_publisher=event_publisher,
    # )
```

---

## 5. Registrar no container raiz

`src/infrastructure/containers/root.py` — adicione o novo sub-container:

```python
from src.infrastructure.containers.core import CoreContainer
from src.infrastructure.containers.identity import IdentityContainer
from src.infrastructure.containers.symphony import SymphonyContainer
from src.infrastructure.containers.billing import BillingContainer  # NEW


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=[
            "src.contexts.identity.adapters.http",
            "src.contexts.billing.adapters.http",  # adicione quando tiver deps.py
        ],
    )

    core = providers.Container(CoreContainer)

    identity = providers.Container(
        IdentityContainer,
        event_publisher=core.event_publisher,
    )

    symphony = providers.Container(
        SymphonyContainer,
        event_publisher=core.event_publisher,
    )

    billing = providers.Container(          # NEW
        BillingContainer,
        event_publisher=core.event_publisher,
    )
```

> Adicione o pacote HTTP ao `wiring_config` somente quando o contexto tiver
> pelo menos um `deps.py` com `@inject`. Antes disso, o pacote vazio não causa
> erros mas também não precisa estar listado.

---

## 6. Atualizar o `.importlinter`

Adicione e atualize os contratos em `.importlinter`:

### 6.1 Novo contrato de camadas

```ini
[importlinter:contract:contexts-respect-layers-billing]
name = Within billing context, layers point inward
type = layers
layers =
    src.contexts.billing.adapters
    src.contexts.billing.use_cases
    src.contexts.billing.domain
exhaustive = false
```

### 6.2 Atualizar `domain-purity`

```ini
[importlinter:contract:domain-purity]
name = Domain layer has no framework imports
type = forbidden
source_modules =
    src.shared
    src.contexts.identity.domain
    src.contexts.symphony.domain
    src.contexts.billing.domain        # NEW
forbidden_modules =
    fastapi
    sqlalchemy
    ...
```

### 6.3 Atualizar `use-cases-purity`

```ini
[importlinter:contract:use-cases-purity]
name = Use cases have no framework or adapter/infra imports
type = forbidden
source_modules =
    src.contexts.identity.use_cases
    src.contexts.symphony.use_cases
    src.contexts.billing.use_cases     # NEW
forbidden_modules =
    ...
    src.contexts.billing.adapters      # NEW
    src.infrastructure
```

### 6.4 Atualizar `adapters-isolation`

```ini
[importlinter:contract:adapters-isolation]
name = Adapter sub-trees don't depend on each other
type = independence
modules =
    src.contexts.identity.adapters.http
    src.contexts.identity.adapters.persistence
    src.contexts.symphony.adapters.http
    src.contexts.symphony.adapters.persistence
    src.contexts.billing.adapters.http         # NEW
    src.contexts.billing.adapters.persistence  # NEW
    src.infrastructure.adapters.events
ignore_imports =
    src.contexts.identity.adapters.http.user.deps -> src.contexts.identity.adapters.persistence.unit_of_work
    src.contexts.identity.adapters.http.user.deps -> src.infrastructure.adapters.events.in_memory_publisher
    src.contexts.identity.adapters.http.user.deps -> src.infrastructure.containers
    src.contexts.identity.adapters.http.user.deps -> src.infrastructure.database
    # adicione as mesmas exceções para billing.deps quando criá-lo
```

### 6.5 Atualizar `bounded-contexts-isolation`

```ini
[importlinter:contract:bounded-contexts-isolation]
name = Bounded contexts don't import from each other
type = independence
modules =
    src.contexts.identity
    src.contexts.symphony
    src.contexts.billing               # NEW
ignore_imports =
    src.contexts.identity.adapters.http.user.deps -> src.infrastructure.containers
    src.contexts.identity.adapters.http.user.deps -> src.infrastructure.database
    # adicione as mesmas exceções para billing.deps quando criá-lo
```

> Verifique que `lint-imports` passa após cada edição no `.importlinter`.
> Contratos incompletos quebram o build silenciosamente se `exhaustive = true`
> (o padrão aqui é `false` para contratos de layers, por isso é seguro).

---

## 7. Fake UoW para testes

Adicione `FakeBillingUoW` em `tests/conftest.py`, seguindo o padrão das existentes:

```python
class FakeBillingUoW:
    """Fake IBillingUnitOfWork para testes de use cases do billing."""

    def __init__(self) -> None:
        # Adicione AsyncMock por repositório conforme os agregados forem criados:
        # self.invoices = AsyncMock()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> "FakeBillingUoW":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True
```

Adicione também o fixture correspondente:

```python
@pytest.fixture
def fake_billing_uow() -> FakeBillingUoW:
    """Fresh FakeBillingUoW per test."""
    return FakeBillingUoW()
```

---

## 8. Adicionar agregados ao novo contexto

Com o esqueleto do contexto no lugar, use a receita de
[how-to-add-aggregate.md](./how-to-add-aggregate.md) para cada agregado —
substituindo `symphony` por `billing` em todos os paths.

Para cada novo agregado, lembre de:

1. Adicionar o repositório ao Protocol `IBillingUnitOfWork` (passo 2).
2. Adicionar o atributo ao `SQLAlchemyBillingUnitOfWork` (passo 3).
3. Adicionar o modelo ao registry (`src/infrastructure/adapters/persistence/registry.py`).
4. Adicionar os use case factories ao `BillingContainer`.
5. Adicionar `orders = AsyncMock()` (ou o nome correto) ao `FakeBillingUoW`.

---

## 9. Atualizar `docs/architecture.md`

Na seção **Bounded Contexts**, adicione o novo contexto à tabela:

```markdown
| `billing` | `src/contexts/billing/` | `Invoice`, ... |
```

---

## 10. Checklist Final

```
[ ] src/contexts/billing/ com __init__.py em todos os sub-pacotes
[ ] src/contexts/billing/domain/unit_of_work.py: IBillingUnitOfWork Protocol
[ ] src/contexts/billing/adapters/persistence/unit_of_work.py: SQLAlchemyBillingUnitOfWork
[ ] src/infrastructure/containers/billing.py: BillingContainer
[ ] src/infrastructure/containers/root.py: billing sub-container registrado
[ ] .importlinter: contrato contexts-respect-layers-billing adicionado
[ ] .importlinter: domain-purity atualizado com billing.domain
[ ] .importlinter: use-cases-purity atualizado com billing.use_cases e billing.adapters
[ ] .importlinter: adapters-isolation atualizado com billing.adapters.http e .persistence
[ ] .importlinter: bounded-contexts-isolation atualizado com billing
[ ] tests/conftest.py: FakeBillingUoW + fixture fake_billing_uow adicionados
[ ] tests/unit/contexts/billing/ e tests/integration/contexts/billing/ criados
[ ] docs/architecture.md: tabela de bounded contexts atualizada
[ ] Agregados criados com how-to-add-aggregate.md (um por um)
[ ] poetry run lint-imports   -> "Contracts: N kept, 0 broken"
[ ] poetry run pytest         -> todos os testes passam
[ ] poetry run mypy src       -> clean
[ ] poetry run ruff check src tests -> clean
```
