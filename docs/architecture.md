# Arquitetura — Clean Architecture / Hexagonal

Este documento é a fonte da verdade para as regras de camadas e dependências do projeto.
**Antes de alterar qualquer arquivo em `src/`, leia este documento.**

As fronteiras são verificadas automaticamente por `poetry run lint-imports` (CI: job `test-arch`)
e por testes em `tests/architecture/`.

---

## Visão Geral

O projeto segue Clean Architecture (também chamada de Hexagonal ou Ports & Adapters).
A regra central é: **setas de import sempre apontam para dentro**.

```
+------------------------------------------------------+
|  src/adapters/http/       (Driving Adapters)         |
|  src/adapters/persistence/ (Driven Adapters)         |
|  src/adapters/events/     (Driven Adapters)          |
|  src/infrastructure/      (DI, Engine, Config)       |
+------------------------------------------------------+
         |  importa de
         v
+------------------------------------------------------+
|  src/use_cases/           (Application / Input Ports)|
+------------------------------------------------------+
         |  importa de
         v
+------------------------------------------------------+
|  src/domain/              (Núcleo puro — Python)     |
|    ├── user/              (Agregado User)             |
|    └── _shared/           (Base: AggregateRoot,      |
|                            DomainEvent, IEventPublisher)|
+------------------------------------------------------+
```

Fluxo de execução de uma request HTTP:

```
HTTP Request
    -> FastAPI route  (src/adapters/http/user/routes/create.py)
    -> CreateUserRequest DTO
    -> CreateUserUseCase.execute()  (src/use_cases/user/create.py)
    -> User.create()  (src/domain/user/entity.py)  [coleta UserCreated]
    -> IUserRepository.save()  (src/domain/user/repository.py — Protocol)
    -> SQLAlchemyUserRepository.save()  (src/adapters/persistence/user/repository.py)
    -> DB commit
    -> to_entity(model)  (mapper)
    -> saved.pull_events()  -> IEventPublisher.publish(events)
    -> UserDTO.from_entity(saved)
    -> CreateUserResponse DTO
    -> JSON response
```

---

## 1. Camada de Domínio — `src/domain/`

**O núcleo puro.** Nenhum import de framework aqui. Se você ver
`from fastapi import`, `from sqlalchemy import`, `from pydantic import`
ou qualquer import de `src.use_cases`, `src.adapters`, `src.infrastructure`
nesta camada, é um erro arquitetural.

### `src/domain/_shared/`

Módulo compartilhado entre agregados. Contém apenas Python puro.

- `events.py` — `DomainEvent`: base frozen dataclass para todos os eventos de domínio.
- `aggregate_root.py` — `AggregateRoot`: base dataclass com `collect_event()` / `pull_events()`.
- `event_publisher.py` — `IEventPublisher`: Protocol (output port) para publicação de eventos.

### Entidades

Possuem identidade (UUID). Dois objetos são iguais se e somente se seus IDs forem iguais.
Implementadas como `@dataclass`. Expõem métodos de comportamento, nunca acopladas a ORM.

Referência no projeto — `src/domain/user/entity.py`:
```python
@dataclass
class User(AggregateRoot):
    email: Email
    name: str
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True

    def deactivate(self) -> None: ...   # coleta UserDeactivated se estava ativo
    def update_name(self, new_name: str) -> None: ...  # coleta UserUpdated se mudou

    @classmethod
    def create(cls, email: Email, name: str) -> "User": ...  # coleta UserCreated
```

### Value Objects

Igualdade estrutural, imutáveis. `@dataclass(frozen=True)`. Validam seus invariantes
no `__post_init__`. Nunca possuem um ID de identidade.

Referência no projeto — `src/domain/user/email.py`:
```python
@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise ValueError(f"Invalid email address: {self.value!r}")
```

### Aggregates e Aggregate Root

Um Aggregate é um cluster consistente de entidades com um único ponto de entrada
(o Aggregate Root). O Root protege os invariantes e é o único objeto que o repositório
persiste e carrega. No projeto atual, `User` é o Aggregate Root do agregado `user`
(agregado trivial com uma só entidade).

`User` herda de `AggregateRoot`, que fornece `collect_event()` e `pull_events()`.
Eventos são coletados nos métodos de domínio e publicados pelo use case após o persist.

### Serviços de Domínio

Para regras que envolvem mais de uma entidade mas não pertencem a nenhuma delas.
Não confundir com Application Service (use case), que orquestra o fluxo.

---

## 2. Camada de Aplicação / Use Cases — `src/use_cases/`

**Os verbos do sistema.** Orquestram; não decidem regras de negócio.
Dependem de Protocols (ports), nunca de implementações concretas.

Fluxo padrão de um use case de mutação:
1. Recebe DTO de entrada (dataclass simples).
2. Carrega o agregado via port (repositório).
3. Chama métodos de domínio (que coletam eventos internamente).
4. Persiste via port.
5. Chama `pull_events()` e publica via `IEventPublisher`.
6. Retorna `UserDTO.from_entity(saved)` embutido no Response DTO.

**Proibido aqui:** imports de `src.adapters`, `src.infrastructure`, `fastapi`,
`sqlalchemy`, `pydantic`, `dependency_injector`.

Referência no projeto — `src/use_cases/user/create.py`:
```python
class CreateUserUseCase:
    def __init__(self, user_repository: IUserRepository, event_publisher: IEventPublisher) -> None:
        self._repo = user_repository
        self._publisher = event_publisher

    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        ...
        saved = await self._repo.save(user)
        events = saved.pull_events()
        if events:
            await self._publisher.publish(events)
        return CreateUserResponse(UserDTO.from_entity(saved), True)
```

### DTOs de saída — `src/use_cases/user/dto.py`

`UserDTO` é um frozen dataclass com `from_entity(user: User)` que converte o agregado
em dados serializáveis. Use cases de mutação retornam `UserDTO` nos Response dataclasses;
o HTTP layer serializa via `to_user_output(dto)` em `serializers.py`.

---

## 3. Output Ports — `src/domain/<entidade>/repository.py`

**Interfaces do repositório usando `typing.Protocol`** (tipagem estrutural), não `abc.ABC`.
Mais pythônico: qualquer classe que implemente os métodos satisfaz o contrato —
sem herança necessária.

Adicione `@runtime_checkable` apenas se houver `isinstance()` em produção.

A inversão de dependência acontece aqui: o use case pede "algo que consiga salvar User",
não "Postgres". Trocar Postgres por Mongo exige mudar apenas a camada de adaptadores.

Referência no projeto — `src/domain/user/repository.py`:
```python
@runtime_checkable
class IUserRepository(Protocol):
    async def find_by_id(self, user_id: UUID) -> Optional[User]: ...
    async def find_by_email(self, email: Email) -> Optional[User]: ...
    async def save(self, user: User) -> User: ...
    async def delete(self, user_id: UUID) -> bool: ...
```

---

## 4. Driven Adapters — `src/adapters/persistence/`

Implementações concretas dos ports (SQLAlchemy, HTTP externo, filas).
Convertem entre entidade de domínio e modelo ORM em um `mapper.py` dedicado.
**O modelo ORM nunca vaza para fora desta camada.**

Implementam o Protocol estruturalmente: nenhuma herança explícita de `IUserRepository`.

Referência no projeto — `src/adapters/persistence/user/repository.py`:
```python
class SQLAlchemyUserRepository:
    """Implements IUserRepository structurally (no explicit inheritance)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> User:
        model = to_model(user)
        self._session.add(model)
        await self._session.commit()
        return to_entity(model)
```

Referência no projeto — `src/adapters/persistence/user/mapper.py`:
```python
def to_entity(model: UserModel) -> User:
    return User(id=model.id, email=Email(model.email), name=model.name, ...)

def to_model(user: User) -> UserModel:
    return UserModel(id=user.id, email=str(user.email), name=user.name, ...)
```

---

## 5. Domain Events

### Ciclo de vida

```
Aggregate method  ->  collect_event()  ->  _events list
Use case          ->  pull_events()    ->  IEventPublisher.publish(events)
```

1. **Coleta**: métodos de domínio chamam `self.collect_event(SomeEvent(...))` internamente.
   O agregado nunca publica diretamente — apenas acumula.
2. **Persist**: o use case persiste o agregado via repositório.
3. **Publish**: após o commit, o use case chama `saved.pull_events()` e passa para
   `IEventPublisher.publish(events)`. Isso garante que eventos só saem após commit bem-sucedido.

### Eventos do agregado User

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

Definido em `src/domain/_shared/event_publisher.py` como `Protocol`:
```python
class IEventPublisher(Protocol):
    async def publish(self, events: list[DomainEvent]) -> None: ...
```

### InMemoryEventPublisher (adapter)

`src/adapters/events/in_memory_publisher.py` — placeholder que loga eventos via
`logging.info`. Para usar um broker real (Kafka, RabbitMQ, Redis Streams),
implemente `async def publish(self, events)` e registre no container como Singleton.

---

## 6. Driving Adapters — `src/adapters/http/`

FastAPI routes, CLI, consumidores de fila. Traduzem protocolo externo → chamada de use case.

Responsabilidades desta camada: validação Pydantic de entrada, autenticação, rate limiting,
serialização HTTP, status codes.

**Proibido aqui:** regra de negócio. `if order.total > 1000:` numa rota é vazamento de domínio.

Referência no projeto — `src/adapters/http/user/routes/create.py`:
```python
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(data: CreateUserInput, create_uc: CreateUserUseCaseDep) -> dict:
    resp = await create_uc.execute(CreateUserRequest(email=data.email, name=data.name))
    if not resp.success:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=resp.error_message)
    return to_user_output(resp.user)
```

---

## 7. Infrastructure — `src/infrastructure/`

Container DI (`dependency-injector`), engine SQLAlchemy, Settings (`pydantic-settings`).

O Container expõe:
- **Singletons**: `config`, `db_engine`, `db_session_factory`, `event_publisher`
- **Factories**: `user_repository`, `create_user_use_case`, ..., `delete_user_use_case`

A sessão fica request-scoped: `get_session` (em `database.py`) é um `AsyncGenerator`
injetado via `Depends(get_session)`. Routes obtêm o use case por
`Provide[Container.<uc>.provider]` em `deps.py`.

Nota sobre a fronteira adapters ↔ infrastructure: `src/adapters/http/user/deps.py`
importa `Container` de `src.infrastructure.container`. Esta é a única exceção intencional
à regra "adapters não importam infrastructure" — é o ponto de costura do DI container.
O contrato `adapters-not-importing-infra` não é aplicado no `.importlinter` por este motivo.

---

## Regra de Dependência (resumo)

| Camada | Pode importar de |
|--------|-----------------|
| `src/domain/` | stdlib apenas |
| `src/use_cases/` | `src/domain/`, stdlib |
| `src/adapters/persistence/` | `src/domain/`, SQLAlchemy, stdlib |
| `src/adapters/events/` | `src/domain/`, stdlib |
| `src/adapters/http/` | `src/domain/`, `src/use_cases/`, FastAPI, Pydantic, `src/infrastructure/container` (exceção intencional) |
| `src/infrastructure/` | tudo |

---

## Convenções Práticas

- Arquivos de HTTP devem ter menos de 80 LOC cada (routes, schemas, serializers).
- Nomes de arquivo em kebab-case para docs; snake_case para módulos Python.
- Sem separadores `# ---` em código.
- Sem herança explícita nos driven adapters — Protocol é suficiente.
- Use `@dataclass` para DTOs (simples, sem validação Pydantic no domínio/use-cases).

---

## Next Steps (não implementados)

- **Transações multi-agregado / UoW**: Unit of Work pattern para operações que tocam mais de um
  agregado. Ativar quando houver 2+ agregados; hoje seria YAGNI com um único agregado `user`.
