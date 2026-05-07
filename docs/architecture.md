# Arquitetura — Clean Architecture / Hexagonal

Este documento é a fonte da verdade para as regras de camadas e dependências do projeto.
**Antes de alterar qualquer arquivo em `src/`, leia este documento.**

As fronteiras são verificadas automaticamente por `poetry run lint-imports` (CI: job `test-arch`)
e por testes em `tests/architecture/`.

---

## Visão Geral

O projeto segue Clean Architecture (também chamada de Hexagonal ou Ports & Adapters)
organizada por **bounded contexts** (fatia vertical). A regra central é:
**setas de import sempre apontam para dentro** — camadas externas dependem de internas,
nunca o contrário.

```
src/
├── shared/                  # Primitivas cross-context (puro Python)
│   ├── aggregate_root.py    # AggregateRoot
│   ├── events.py            # DomainEvent
│   ├── event_publisher.py   # IEventPublisher (Protocol)
│   └── agentic/             # Kernel agentic — Protocols + utilities
│       ├── retry.py         # classify_failure / compute_delay / RetryConfig
│       ├── gate.py          # Gate ABC / GateRunner / GateOutcome
│       ├── agent_runner.py  # IAgentRunner Protocol + TurnResult
│       └── workspace.py     # IWorkspaceManager Protocol + Workspace VO
│
├── contexts/
│   ├── identity/            # Bounded Context: identidade de usuários
│   │   ├── domain/          # Núcleo puro — entidades, VOs, ports, UoW Protocol
│   │   ├── use_cases/       # Application Services (verbos do sistema)
│   │   └── adapters/
│   │       ├── http/        # Driving adapter: FastAPI routes
│   │       └── persistence/ # Driven adapter: SQLAlchemy + UoW adapter
│   │
│   └── symphony/            # Bounded Context: runs, specs, plans
│       ├── domain/
│       ├── use_cases/
│       └── adapters/
│           ├── http/        # Placeholders (sem endpoints ainda)
│           └── persistence/
│
└── infrastructure/          # DI container, engine, config
    ├── config.py
    ├── database.py
    ├── containers/
    │   ├── core.py          # CoreContainer — singletons globais
    │   ├── identity.py      # IdentityContainer — UoW + use cases
    │   ├── symphony.py      # SymphonyContainer — UoW + use cases
    │   └── root.py          # Container raiz — compõe os três acima
    └── adapters/
        ├── events/
        │   └── in_memory_publisher.py
        └── persistence/
            ├── base.py      # DeclarativeBase
            └── registry.py  # Registra todos os modelos ORM
```

Diagrama de dependência (setas = "importa de"):

```
infrastructure  ──────────────────────────────> tudo
adapters/http   ──> use_cases, domain, shared, infrastructure/containers
adapters/persist──> domain, shared, sqlalchemy
use_cases       ──> domain, shared
domain          ──> shared, stdlib
shared          ──> stdlib apenas
```

### Fluxo de uma request HTTP

```
HTTP Request
    -> FastAPI route
       (src/contexts/identity/adapters/http/user/routes/create.py)
    -> CreateUserInput (Pydantic — validação de entrada)
    -> deps.py constrói SQLAlchemyIdentityUnitOfWork(session)
       e chama factory(uow=..., event_publisher=...)
    -> CreateUserUseCase.execute(CreateUserRequest)
    -> async with self._uow:
           uow.users.find_by_email(email)   # flush-safe read
           User.create(email, name)         # coleta UserCreated
           saved = await uow.users.save(user)  # session.flush() — sem commit
           await uow.commit()              # transação confirmada
           events = user.pull_events()     # do aggregate de entrada
    -> if events: await publisher.publish(events)  # após commit
    -> UserDTO.from_entity(saved)
    -> to_user_output(dto)
    -> JSON response 201
```

---

## Bounded Contexts

Um **bounded context** é uma fronteira explícita dentro da qual um modelo de domínio
tem significado coerente. Contextos distintos usam linguagens, entidades e regras
independentes — e **nunca se importam diretamente**.

O projeto tem três contextos:

| Contexto | Raiz em `src/` | Agrega |
|----------|---------------|--------|
| `identity` | `src/contexts/identity/` | `User` |
| `symphony` | `src/contexts/symphony/` | `Run`, `Spec`, `Plan` |
| `tenancy` | `src/contexts/tenancy/` | `Organization` (Phase 2) |

O contrato `bounded-contexts-isolation` no `.importlinter` aplica essa separação
automaticamente: os três contextos são declarados `independence` — qualquer
import direto entre eles quebra o build.

A única exceção intencional é `deps.py` (driving adapter) importar
`src.infrastructure.containers`, que é o ponto de costura do DI. Isso não é
importação direta entre contextos.

Ver `.importlinter` para os 7 contratos completos.

---

## 1. Camada de Domínio — `src/contexts/<context>/domain/`

**O núcleo puro.** Nenhum import de framework. Se você ver
`from fastapi import`, `from sqlalchemy import`, `from pydantic import`
ou qualquer import de `use_cases`, `adapters`, `infrastructure` nesta camada,
é um erro arquitetural.

### `src/shared/`

Primitivas reutilizáveis entre todos os contextos. Também proibido importar frameworks.

- `events.py` — `DomainEvent`: base `@dataclass(frozen=True)` com `event_id` (UUID) e
  `occurred_at` (datetime) gerados automaticamente.
- `aggregate_root.py` — `AggregateRoot`: base dataclass com `collect_event()` /
  `pull_events()`.
- `event_publisher.py` — `IEventPublisher`: Protocol (output port) para publicação
  de eventos.

### Entidades

Possuem identidade (UUID). Implementadas como `@dataclass`. Expõem métodos de
comportamento, nunca acopladas a ORM.

Referência — `src/contexts/identity/domain/user/entity.py`:
```python
@dataclass
class User(AggregateRoot):
    email: Email
    name: str
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def deactivate(self) -> None: ...     # coleta UserDeactivated
    def update_name(self, new_name: str) -> None: ...  # coleta UserUpdated
    def activate(self) -> None: ...
    def can_login(self) -> bool: ...

    @classmethod
    def create(cls, email: Email, name: str) -> "User": ...  # coleta UserCreated
```

### Value Objects

Igualdade estrutural, imutáveis. `@dataclass(frozen=True)`. Validam invariantes
no `__post_init__`.

Referência — `src/contexts/identity/domain/user/email.py`:
```python
@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise ValueError(f"Invalid email address: {self.value!r}")
```

### Aggregate Root

`User` herda de `AggregateRoot` (`src/shared/aggregate_root.py`):
```python
@dataclass
class AggregateRoot:
    _events: list[DomainEvent] = field(init=False, default_factory=list, ...)

    def collect_event(self, event: DomainEvent) -> None: ...
    def pull_events(self) -> list[DomainEvent]: ...  # retorna e limpa a lista
```

Eventos são coletados nos métodos de domínio e publicados pelo use case
**após** o commit da transação.

### Serviços de Domínio

Para regras que envolvem mais de uma entidade mas não pertencem a nenhuma delas.
Não confundir com Application Service (use case), que orquestra o fluxo.

### Constants e Validators de Domínio

Quando uma constante (filename, magic number, status) ou uma checagem de
invariante (`if not x.strip(): raise ValueError(...)`) repete em mais de
um lugar do mesmo contexto, extrair para módulos dedicados na própria
camada de domínio (puro Python, importáveis por use_cases e adapters):

- `domain/constants.py` — literais de contrato (paths, filenames, ceilings).
  Exemplo: `src/contexts/symphony/domain/constants.py` com
  `SYMPHONY_WORKSPACE_DIR = ".symphony"`, `MAX_ORCHESTRATION_ITERATIONS`,
  `MIN_ARTIFACT_VERSION`.
- `domain/validators.py` — funções puras que reutilizam invariantes triviais.
  Exemplo: `ensure_non_blank(value, field_name)` substitui o snippet
  `if not x.strip(): raise ValueError(...)` em cerca de 17 locais nas
  entidades do contexto symphony.

Um teste arquitetural anti-regressão (`tests/architecture/test_no_inline_constants.py`)
falha se um literal proibido voltar a aparecer fora do `constants.py`.

### Base classes para padrões repetidos

Quando dois ou mais aggregates compartilham 100% do ciclo de vida
(write-once approval, soft-delete, etc.), abstrair uma base
`@dataclass` que herde de `AggregateRoot` e expõe os comportamentos
compartilhados — subclasses fornecem apenas os eventos tipados via
métodos hook.

Referência — `src/contexts/symphony/domain/approval/aggregate.py`:
```python
@dataclass
class ApprovedAggregate(AggregateRoot):
    """Write-once approval base reused por Spec e Plan."""

    run_id: UUID
    version: int
    content: str
    # ... campos de verdict ...

    def approve(self, by: str) -> None:
        self._guard_pending()
        ensure_non_blank(by, "Approver identifier")
        self.approved_by = by
        self.approved_at = datetime.now(timezone.utc)
        self.collect_event(self._make_approved_event(by))

    def _make_approved_event(self, by: str) -> DomainEvent:
        """Subclass hook — ``raise NotImplementedError`` no base."""
        raise NotImplementedError(...)
```

`Spec` e `Plan` herdam, sobrescrevem os 3 hooks `_make_*_event` para
emitir `SpecApproved` / `PlanApproved` etc, e ficam em ~45 linhas cada
(vs. 88 quando duplicadas).

---

## 2. Camada de Aplicação / Use Cases — `src/contexts/<context>/use_cases/`

**Os verbos do sistema.** Orquestram; não decidem regras de negócio.
Dependem de Protocols (ports), nunca de implementações concretas.

**Proibido aqui:** imports de `adapters`, `infrastructure`, `fastapi`,
`sqlalchemy`, `pydantic`, `dependency_injector`.

### Padrão UoW nos use cases de mutação

Use cases recebem `uow: I<Context>UnitOfWork` (não repositório diretamente).
O UoW é o único ponto de commit da transação:

```python
class CreateUserUseCase:
    def __init__(
        self,
        uow: IIdentityUnitOfWork,
        event_publisher: IEventPublisher,
    ) -> None:
        self._uow = uow
        self._publisher = event_publisher

    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        # validação de entrada antes do UoW
        try:
            email = Email(request.email)
        except ValueError as exc:
            return CreateUserResponse(None, False, str(exc))

        async with self._uow:
            if await self._uow.users.find_by_email(email):
                return CreateUserResponse(None, False, "Email already registered.")
            user = User.create(email=email, name=request.name)
            saved = await self._uow.users.save(user)  # flush, sem commit
            await self._uow.commit()                   # transação confirmada
            events = user.pull_events()                # do aggregate de entrada

        if events:
            await self._publisher.publish(events)      # após commit
        return CreateUserResponse(UserDTO.from_entity(saved), True)
```

> **Regra crítica:** eventos são coletados do aggregate **de entrada** (`user`),
> nunca do retorno do repositório (`saved`). O adapter pode retornar uma instância
> nova via `to_entity(model)`, que não carrega os eventos coletados.
> Ver § Domain Events — Pitfall abaixo.

Use cases de leitura (`get`, `list`) recebem apenas `uow` (sem publisher):
```python
class GetUserUseCase:
    def __init__(self, uow: IIdentityUnitOfWork) -> None:
        self._uow = uow
```

### DTOs de saída

`UserDTO` é um frozen dataclass com `from_entity(user: User)`. Use cases de mutação
retornam `UserDTO` nos Response dataclasses; o HTTP layer serializa via
`to_user_output(dto)` em `serializers.py`.

---

## 3. Output Ports — repositórios e UoW

### Repositórios — `src/contexts/<context>/domain/<aggregate>/repository.py`

**Interfaces usando `typing.Protocol`** (tipagem estrutural), não `abc.ABC`.
A inversão de dependência acontece aqui.

Referência — `src/contexts/identity/domain/user/repository.py`:
```python
@runtime_checkable
class IUserRepository(Protocol):
    async def find_by_id(self, user_id: UUID) -> User | None: ...
    async def find_by_email(self, email: Email) -> User | None: ...
    async def list(self, limit: int = 20, offset: int = 0) -> list[User]: ...
    async def save(self, user: User) -> User: ...
    async def update(self, user: User) -> User: ...
    async def delete(self, user_id: UUID) -> bool: ...
```

### Unit of Work Protocol — `src/contexts/<context>/domain/unit_of_work.py`

O UoW é o output port da transação. Vive na camada de domínio para que use cases
dependam de uma abstração, não de SQLAlchemy.

`src/contexts/identity/domain/unit_of_work.py`:
```python
@runtime_checkable
class IIdentityUnitOfWork(Protocol):
    users: "IUserRepository"

    async def __aenter__(self) -> "IIdentityUnitOfWork": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
```

`src/contexts/symphony/domain/unit_of_work.py`:
```python
@runtime_checkable
class ISymphonyUnitOfWork(Protocol):
    runs: "IRunRepository"
    specs: "ISpecRepository"
    plans: "IPlanRepository"

    async def __aenter__(self) -> "ISymphonyUnitOfWork": ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
```

---

## 4. Driven Adapters — `src/contexts/<context>/adapters/persistence/`

Implementações concretas dos ports (SQLAlchemy).
**O modelo ORM nunca vaza para fora desta camada.**

Implementam os Protocols estruturalmente: nenhuma herança explícita.

### Repositórios concretos

Repositórios chamam `session.flush()` — **nunca `session.commit()`**.
O commit é responsabilidade exclusiva do UoW.

Referência — `src/contexts/identity/adapters/persistence/user/repository.py`:
```python
class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> User:
        model = to_model(user)
        self._session.add(model)
        await self._session.flush()      # stages, sem commit
        await self._session.refresh(model)
        return to_entity(model)
```

O mapper (`mapper.py`) converte entre entidade de domínio e modelo ORM:
```python
def to_entity(model: UserModel) -> User:
    return User(id=model.id, email=Email(model.email), name=model.name, ...)

def to_model(user: User) -> UserModel:
    return UserModel(id=user.id, email=str(user.email), name=user.name, ...)
```

### UoW Adapter — `src/contexts/<context>/adapters/persistence/unit_of_work.py`

O adapter recebe a `AsyncSession` e constrói os repositórios com ela.
Satisfaz o Protocol estruturalmente.

Referência — `src/contexts/identity/adapters/persistence/unit_of_work.py`:
```python
class SQLAlchemyIdentityUnitOfWork:
    users: SQLAlchemyUserRepository

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = SQLAlchemyUserRepository(session)

    async def __aenter__(self) -> "SQLAlchemyIdentityUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
```

O adapter do symphony (`SQLAlchemySymphonyUnitOfWork`) segue a mesma forma,
expondo `runs`, `specs` e `plans` como atributos.

### Registry de modelos ORM

`src/infrastructure/adapters/persistence/registry.py` — único lugar com
`# noqa: F401` para side-effects de registro:
```python
import src.contexts.identity.adapters.persistence.user.model   # noqa: F401
import src.contexts.symphony.adapters.persistence.run.model    # noqa: F401
import src.contexts.symphony.adapters.persistence.spec.model   # noqa: F401
import src.contexts.symphony.adapters.persistence.plan.model   # noqa: F401
```

---

## 5. Domain Events

### Ciclo de vida

```
Aggregate method  ->  collect_event()  ->  _events list
Use case (dentro do async with uow):
    uow.users.save(user)    # flush
    uow.commit()            # transação confirmada
    events = user.pull_events()
# fora do async with uow:
if events:
    publisher.publish(events)
```

1. **Coleta**: métodos de domínio chamam `self.collect_event(SomeEvent(...))`.
2. **Flush**: repositório persiste via `session.flush()` — sem commit ainda.
3. **Commit**: `uow.commit()` finaliza a transação.
4. **Publish**: após o commit, o use case publica via `IEventPublisher`.
   Eventos saem somente após commit bem-sucedido.

### Pitfall — qual instância carrega os eventos

> **Atenção:** use cases devem sempre coletar eventos do aggregate **de entrada**,
> nunca do retorno do repositório.

`to_entity(model)` reconstrói um aggregate **novo** com lista de eventos vazia.
Se o use case fizer `saved.pull_events()`, em produção receberá `[]` — eventos
descartados silenciosamente. Em testes com `AsyncMock` o mock devolve a mesma
referência Python que entrou, então `saved is user` e os eventos estão lá:
**os testes passam, mascarando o bug em produção.**

Padrão correto para mutação que cria:

```python
saved = await self._uow.users.save(user)   # persist (pode retornar objeto fresh)
events = user.pull_events()                # <-- do ORIGINAL, não de saved
if events:
    await self._publisher.publish(events)
return CreateXResponse(UserDTO.from_entity(saved), True)  # DTO do refreshed
```

O DTO vem de `saved` (campos hidratados pelo DB — timestamps, sequences).
Os eventos vêm de `user` (coletados pelos métodos de domínio antes do persist).

Anti-padrões a evitar:

```python
# Errado — coleta do retorno do repo (bug silencioso em produção)
saved = await self._uow.users.save(user)
events = saved.pull_events()

# Errado — publica antes do persist (ghost event se o persist falhar)
events = user.pull_events()
await self._publisher.publish(events)
saved = await self._uow.users.save(user)
```

A regressão só é detectável com teste de integração usando o adapter real
(não `AsyncMock`). Referência: `tests/integration/identity/test_event_publication.py`.

### Eventos do agregado User

`src/contexts/identity/domain/user/events.py`:
```python
@dataclass(frozen=True)
class UserCreated(DomainEvent):
    user_id: UUID; email: str; name: str

@dataclass(frozen=True)
class UserDeactivated(DomainEvent):
    user_id: UUID

@dataclass(frozen=True)
class UserUpdated(DomainEvent):
    user_id: UUID

@dataclass(frozen=True)
class UserDeleted(DomainEvent):
    user_id: UUID
```

### IEventPublisher (port)

`src/shared/event_publisher.py`:
```python
@runtime_checkable
class IEventPublisher(Protocol):
    async def publish(self, events: list[DomainEvent]) -> None: ...
```

### InMemoryEventPublisher (adapter)

`src/infrastructure/adapters/events/in_memory_publisher.py` — loga eventos via
`logging.info`. Para broker real (Kafka, RabbitMQ, Redis Streams), implemente
o método `publish` e registre no `CoreContainer` como Singleton.

---

## 6. Driving Adapters — `src/contexts/<context>/adapters/http/`

FastAPI routes. Traduzem protocolo HTTP → chamada de use case.

Responsabilidades: validação Pydantic de entrada, serialização HTTP, status codes.

**Proibido aqui:** regra de negócio.

Referência — `src/contexts/identity/adapters/http/user/routes/create.py`:
```python
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(data: CreateUserInput, create_uc: CreateUserUseCaseDep) -> dict:
    resp = await create_uc.execute(CreateUserRequest(email=data.email, name=data.name))
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    assert resp.user is not None
    return to_user_output(resp.user)
```

Estrutura do pacote HTTP por contexto:

```
src/contexts/identity/adapters/http/user/
├── __init__.py       # re-exporta router; importa routes/ (side-effect)
├── router.py         # APIRouter(prefix="/users", tags=["users"])
├── schemas.py        # Pydantic BaseModel — validação de entrada
├── serializers.py    # DTO → dict de saída
├── deps.py           # @inject + wiring do DI container
└── routes/
    ├── __init__.py
    ├── create.py
    ├── get.py
    ├── list.py
    ├── update.py
    └── delete.py
```

O `deps.py` é o **DI seam**: único ponto onde o driving adapter importa
`src.infrastructure.containers` e `src.infrastructure.database`.
Essa exceção é intencional e explicitamente listada em `ignore_imports`
nos contratos `adapters-isolation` e `bounded-contexts-isolation` do `.importlinter`.

---

## 7. Unit of Work

### Por que por contexto?

O UoW é definido **por bounded context**, não globalmente. Um UoW único cruzando
`identity` e `symphony` quebraria o contrato `bounded-contexts-isolation`.
Cada contexto tem seu próprio Protocol no domínio e sua própria implementação
no adapter de persistência.

### Contrato

- **Protocol** em `src/contexts/<context>/domain/unit_of_work.py` — camada de domínio.
- **Adapter** em `src/contexts/<context>/adapters/persistence/unit_of_work.py` — camada
  de persistência.

### Regras

| Quem | O que faz |
|------|-----------|
| Repositório | Chama `session.flush()` — stages mudanças sem commitar |
| Use case (dentro do `async with uow`) | Chama `await uow.commit()` — única transação |
| Use case (fora do `async with uow`) | Publica eventos via `IEventPublisher` |
| `__aexit__` do UoW | Faz rollback automático se houver exceção |

### Testes de use case com Fake UoW

Para unit tests, use `FakeIdentityUoW` / `FakeSymphonyUoW` de `tests/conftest.py`.
Elas implementam o Protocol estruturalmente (sem herança), expõem repos como
`AsyncMock`, e rastreiam `committed` e `rolled_back`:

```python
class FakeIdentityUoW:
    def __init__(self) -> None:
        self.users = AsyncMock()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> "FakeIdentityUoW": return self
    async def __aexit__(self, *args) -> None: pass
    async def commit(self) -> None: self.committed = True
    async def rollback(self) -> None: self.rolled_back = True
```

---

## 8. Infrastructure — `src/infrastructure/`

Container DI (`dependency-injector`), engine SQLAlchemy, Settings (`pydantic-settings`).

O Container é dividido em três camadas:

### CoreContainer (`containers/core.py`)

Singletons globais compartilhados por todos os contextos:
- `config` — `Settings` (pydantic-settings)
- `db_engine` — `AsyncEngine`
- `db_session_factory` — `async_sessionmaker[AsyncSession]`
- `event_publisher` — `InMemoryEventPublisher`

### IdentityContainer (`containers/identity.py`)

Factories para o contexto de identidade:
- `identity_uow` — `Factory(SQLAlchemyIdentityUnitOfWork)`
- `create_user_use_case`, `get_user_use_case`, `list_users_use_case`,
  `update_user_use_case`, `delete_user_use_case` — todos `Factory(...)` com
  `uow=identity_uow` e `event_publisher` (quando necessário).

Recebe `event_publisher` via `providers.Dependency` — injetado pelo root container.

### SymphonyContainer (`containers/symphony.py`)

Factories para o contexto symphony:
- `symphony_uow` — `Factory(SQLAlchemySymphonyUnitOfWork)`
- Use cases para `run`, `spec`, `plan` — todos `Factory(...)`.

### Constants em adapters de infraestrutura

Cada adapter complexo de infraestrutura mantém um `constants.py` próprio
para magic numbers, regex patterns e timeouts — `domain/` não importa de
infra, então literais infra ficam dentro de cada subdiretório:

- `infrastructure/adapters/workflow/constants.py` — defaults de polling, timeouts
  do agent/turn/stall, deltas do retry config, `ENV_VAR_PATTERN`.
- `infrastructure/adapters/agent_runner/constants.py` — `MAX_PROMPT_BYTES`,
  `KILL_TIMEOUT_SECONDS`.
- `infrastructure/adapters/workspace/constants.py` — hook timeouts, output cap,
  regex de sanitização de chave, `ABORT_ON_FAILURE_HOOKS`.

### HTTP factory para use cases (eliminar duplicação de `deps.py`)

Quando múltiplos sub-routers (run/spec/plan) precisam do mesmo padrão
`Provide[Container.<context>.<uc>.provider]` + UoW per-request +
publisher opcional, extrair um factory genérico em
`adapters/http/use_case_deps.py`:

```python
def make_use_case_dep(provider: Any, *, with_publisher: bool) -> Callable[..., Any]:
    """Factory que monta uma FastAPI dependency com @inject."""
    if with_publisher:
        @inject
        def dep(
            session: SessionDep,
            factory: Callable[..., T] = Depends(provider),
            publisher: InMemoryEventPublisher = Depends(_core_event_publisher),
        ) -> T:
            return factory(uow=SQLAlchemySymphonyUnitOfWork(session), event_publisher=publisher)
        return dep
    # ... read-only variant
```

Cada `<entity>/deps.py` vira um thin shim de ~25 linhas declarando
`get_*_use_case = make_use_case_dep(...)` + os aliases `Annotated[...,
Depends(...)]`. As exceções correspondentes em `.importlinter`
ficam centralizadas em `use_case_deps`.

### Dedupe de configs entre infra e shared

Quando uma config Pydantic do operador (YAML config) e uma config dataclass
runtime convergem, manter o Pydantic como **schema** (sufixo `Schema`) e
expor um método `to_runtime()` que projeta para o dataclass do
`shared/`. Exemplo: `RetryConfigSchema.to_runtime() -> shared.agentic.retry.RetryConfig`
elimina dois `RetryConfig` divergentes preservando os contratos de cada layer.

### Container raiz (`containers/root.py`)

Compõe os três sub-containers e define `wiring_config`:

```python
class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["src.contexts.identity.adapters.http"],
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
```

### Sessão request-scoped

`get_session` (`src/infrastructure/database.py`) lê a `db_session_factory` do
container armazenado em `app.state.container` (via `request`). Isso mantém o engine
e a factory como singletons long-lived enquanto a sessão é scoped por request.

```python
async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory = get_container(request).core.db_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

> Nota: `get_session` faz commit no nível do request como fallback de segurança.
> O commit do UoW dentro do use case é o commit de negócio real — eles coexistem
> porque `session.commit()` num contexto já commitado é idempotente.

---

## Regra de Dependência (resumo)

| Camada | Pode importar de |
|--------|-----------------|
| `src/shared/` | stdlib apenas |
| `src/contexts/*/domain/` | `src/shared/`, stdlib |
| `src/contexts/*/use_cases/` | `src/contexts/*/domain/`, `src/shared/`, stdlib |
| `src/contexts/*/adapters/persistence/` | `src/contexts/*/domain/`, `src/shared/`, SQLAlchemy, stdlib |
| `src/contexts/*/adapters/events/` | `src/shared/`, stdlib |
| `src/contexts/*/adapters/http/` | `src/contexts/*/domain/`, `src/contexts/*/use_cases/`, FastAPI, Pydantic, `src/infrastructure/containers` (exceção intencional em deps.py) |
| `src/infrastructure/` | tudo |

Contextos são independentes entre si: `src/contexts/identity` e
`src/contexts/symphony` **não se importam diretamente**.

---

## Convenções Práticas

- Arquivos HTTP com menos de 80 LOC cada (routes, schemas, serializers).
- Nomes de arquivo em kebab-case para docs; snake_case para módulos Python.
- Sem separadores `# ---` em código.
- Sem herança explícita nos driven adapters — Protocol é suficiente.
- `@dataclass` para DTOs (sem validação Pydantic no domínio/use-cases).
- Imports absolutos: `from src.contexts.identity.domain.user.entity import User`.
  Imports relativos são proibidos (ruff rule `TID252`).

---

## Next Steps (não implementados)

- **Symphony HTTP routes**: os pacotes `src/contexts/symphony/adapters/http/{run,spec,plan,backlog}/`
  existem com `__init__.py` vazio. Nenhum endpoint exposto ainda.
- **Backlog Linear adapter**: `src/contexts/symphony/domain/backlog/adapter.py` define
  o port `IBacklogAdapter`. Nenhuma implementação httpx concreta existe.
- **Cross-context transactions**: quando uma operação precisar tocar `identity` +
  `symphony` atomicamente, usar Saga (coreografia via eventos ou orquestração). Hoje
  os contextos são isolados e isso seria YAGNI.

---

Ver também:
- [how-to-add-aggregate.md](./how-to-add-aggregate.md) — receita para adicionar um
  agregado dentro de um contexto existente.
- [how-to-add-bounded-context.md](./how-to-add-bounded-context.md) — receita para
  criar um novo bounded context do zero.
