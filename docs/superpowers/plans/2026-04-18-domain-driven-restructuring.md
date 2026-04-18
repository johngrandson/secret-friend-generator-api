# Domain-Driven Restructuring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure python-starter from flat `src/app/` into 3-layer domain-driven architecture (domain/api/shared) with SA 2.0 + Pydantic v2 upgrades.

**Architecture:** Move business logic to `src/domain/`, HTTP adapters to `src/api/`, cross-cutting concerns to `src/shared/`. Each domain context (group, participant, secret_friend) owns its models, schemas, services, and repositories. API routes are thin adapters that delegate to domain services.

**Tech Stack:** Python 3.11+, FastAPI 0.100, SQLAlchemy 2.0.13, Pydantic 2.10, PostgreSQL 15, pytest 7.4

**Spec:** `docs/superpowers/specs/2026-04-18-domain-driven-restructuring-design.md`

---

## Task 1: Create directory structure and shared infrastructure

**Files:**
- Create: `src/__init__.py`
- Create: `src/domain/__init__.py`
- Create: `src/domain/shared/__init__.py`
- Create: `src/domain/shared/database_base.py`
- Create: `src/domain/shared/database_session.py`
- Create: `src/domain/shared/database_transaction.py`
- Create: `src/domain/shared/domain_exceptions.py`
- Create: `src/domain/shared/domain_validators.py`
- Create: `src/domain/group/__init__.py`
- Create: `src/domain/participant/__init__.py`
- Create: `src/domain/secret_friend/__init__.py`
- Create: `src/api/__init__.py`
- Create: `src/api/auth/__init__.py`
- Create: `src/api/group/__init__.py`
- Create: `src/api/participant/__init__.py`
- Create: `src/api/secret_friend/__init__.py`
- Create: `src/web/__init__.py`
- Create: `src/shared/__init__.py`
- Create: `src/shared/utils/__init__.py`

- [ ] **Step 1: Create all `__init__.py` files for package structure**

```bash
mkdir -p src/domain/shared src/domain/group src/domain/participant src/domain/secret_friend
mkdir -p src/api/auth src/api/group src/api/participant src/api/secret_friend
mkdir -p src/web src/shared/utils

touch src/__init__.py
touch src/domain/__init__.py src/domain/shared/__init__.py
touch src/domain/group/__init__.py src/domain/participant/__init__.py src/domain/secret_friend/__init__.py
touch src/api/__init__.py src/api/auth/__init__.py
touch src/api/group/__init__.py src/api/participant/__init__.py src/api/secret_friend/__init__.py
touch src/web/__init__.py src/shared/__init__.py src/shared/utils/__init__.py
```

- [ ] **Step 2: Create `src/domain/shared/database_base.py`**

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Note: replaces legacy `@as_declarative()` pattern from `src/app/database/base_class.py`. SA 2.0 uses `DeclarativeBase` class inheritance. The old `Base` auto-generated `__tablename__` from class name — each model already declares `__tablename__` explicitly, so this feature is not needed.

- [ ] **Step 3: Create `src/domain/shared/database_session.py`**

```python
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.shared.app_config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Create `src/domain/shared/database_transaction.py`**

```python
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction(db_session: Session):
    """Atomic operation wrapper. Repos must use flush(), not commit().
    Services call this for multi-step operations that need atomicity.
    Do not nest — each service method should be the single transaction boundary."""
    try:
        yield db_session
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
```

- [ ] **Step 5: Create `src/domain/shared/domain_exceptions.py`**

```python
class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass
```

- [ ] **Step 6: Create `src/domain/shared/domain_validators.py`**

```python
import re


def validate_email(value: str) -> str:
    """Reusable email validator. Use inside Pydantic @field_validator."""
    value = value.strip().lower()
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
        raise ValueError("Invalid email address")
    if len(value) > 160:
        raise ValueError("Email must be 160 characters or less")
    return value


def validate_url(value: str) -> str:
    """Validates and normalizes URL. Prepends https:// if scheme absent."""
    value = value.strip()
    if not value:
        raise ValueError("URL cannot be blank")
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    if not re.match(r"https?://[^\s/$.?#].[^\s]*", value):
        raise ValueError("Invalid URL")
    return value


def validate_not_blank(value: str) -> str:
    """Trims whitespace and ensures value is not empty."""
    value = value.strip()
    if not value:
        raise ValueError("Field cannot be blank")
    return value
```

- [ ] **Step 7: Commit**

```bash
git add src/domain/ src/api/ src/web/ src/shared/ src/__init__.py
git commit -m "feat: create 3-layer directory structure and shared domain infrastructure"
```

---

## Task 2: Create shared layer (config, utils)

**Files:**
- Create: `src/shared/app_config.py`
- Create: `src/shared/utils/hashing_utils.py`
- Create: `src/shared/rate_limiter_config.py`
- Create: `src/shared/scheduler_config.py`
- Create: `src/shared/instance_manager.py`

- [ ] **Step 1: Create `src/shared/app_config.py`**

Merges `src/app/common/utils/config.py` into a single config source. Trimmed to what the project actually uses — no starlette.config, no MJML, no PKCE, no multi-tenant Alembic paths.

```python
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

log = logging.getLogger(__name__)


class Settings:
    PROJECT_NAME: str = "Secret Santa Generator"
    PROJECT_VERSION: str = "1.0.0"

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tdd")
    DATABASE_URL: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    ENV: str = os.getenv("ENV", "local")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")

    # Sentry (optional)
    SENTRY_ENABLED: str = os.getenv("SENTRY_ENABLED", "")
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")


settings = Settings()
```

- [ ] **Step 2: Create `src/shared/utils/hashing_utils.py`**

```python
import secrets


class Hasher:
    @staticmethod
    def generate_group_token() -> str:
        """Generate a URL-safe random token for group links."""
        return secrets.token_urlsafe(16)
```

- [ ] **Step 3: Create `src/shared/rate_limiter_config.py`**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

- [ ] **Step 4: Create `src/shared/scheduler_config.py`**

Copy `src/app/scheduler.py` content with updated import:

```python
import logging
import time
from multiprocessing.pool import ThreadPool

import schedule

log = logging.getLogger(__name__)


class Scheduler:
    """Simple scheduler class that holds all scheduled functions."""

    registered_tasks = []
    running = True

    def __init__(self, num_workers=100):
        self.pool = ThreadPool(processes=num_workers)

    def add(self, job, *args, **kwargs):
        def decorator(func):
            if not kwargs.get("name"):
                name = func.__name__
            else:
                name = kwargs.pop("name")

            self.registered_tasks.append(
                {"name": name, "func": func, "job": job.do(self.pool.apply_async, func)}
            )

        return decorator

    def remove(self, task):
        schedule.cancel_job(task["job"])

    def start(self):
        log.info("Starting scheduler...")
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        log.debug("Stopping scheduler...")
        self.pool.close()
        self.running = False


scheduler = Scheduler()


def stop_scheduler(signum, frame):
    scheduler.stop()
```

- [ ] **Step 5: Create `src/shared/instance_manager.py`**

```python
import logging

log = logging.getLogger(__name__)


class InstanceManager:
    """Dynamic class loader for plugin-style module instantiation."""

    def __init__(self, class_list=None, instances=True):
        if class_list is None:
            class_list = []
        self.instances = instances
        self.update(class_list)

    def get_class_list(self):
        return self.class_list

    def add(self, class_path):
        self.cache = None
        if class_path not in self.class_list:
            self.class_list.append(class_path)

    def remove(self, class_path):
        self.cache = None
        self.class_list.remove(class_path)

    def update(self, class_list):
        self.cache = None
        self.class_list = class_list

    def all(self):
        class_list = list(self.get_class_list())
        if not class_list:
            self.cache = []
            return []

        if self.cache is not None:
            return self.cache

        results = []
        for cls_path in class_list:
            module_name, class_name = cls_path.rsplit(".", 1)
            try:
                module = __import__(module_name, {}, {}, class_name)
                cls = getattr(module, class_name)
                if self.instances:
                    results.append(cls())
                else:
                    results.append(cls)
            except Exception as e:
                log.exception(f"Unable to import {cls_path}. Reason: {e}")
                continue

        self.cache = results
        return results
```

- [ ] **Step 6: Commit**

```bash
git add src/shared/
git commit -m "feat: create shared layer with config, utils, rate limiter, scheduler"
```

---

## Task 3: Migrate group domain context

**Files:**
- Create: `src/domain/group/group_schemas.py`
- Create: `src/domain/group/group_model.py`
- Create: `src/domain/group/group_repository.py`
- Create: `src/domain/group/group_service.py`

- [ ] **Step 1: Create `src/domain/group/group_schemas.py`**

```python
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    santa = "santa"
    chocolate = "chocolate"
    frenemy = "frenemy"
    book = "book"
    wine = "wine"
    easter = "easter"


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=4)
    description: str
    category: CategoryEnum = CategoryEnum.santa


class GroupRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str
    category: CategoryEnum = CategoryEnum.santa
    link_url: Optional[str] = None
    participants: list["ParticipantBase"] = []


class GroupList(BaseModel):
    model_config = {"from_attributes": True}

    groups: list[GroupRead] = Field(default_factory=list)


# Deferred import to avoid circular dependency
from src.domain.participant.participant_schemas import ParticipantBase  # noqa: E402

GroupRead.model_rebuild()
```

- [ ] **Step 2: Create `src/domain/group/group_model.py`**

```python
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.shared.database_base import Base
from src.domain.group.group_schemas import CategoryEnum


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    link_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    category: Mapped[CategoryEnum] = mapped_column(
        SQLAlchemyEnum(CategoryEnum), nullable=False, default=CategoryEnum.santa
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, onupdate=lambda: datetime.now(timezone.utc)
    )

    participants: Mapped[list["Participant"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
```

- [ ] **Step 3: Create `src/domain/group/group_repository.py`**

```python
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.group.group_model import Group
from src.domain.group.group_schemas import GroupCreate
from src.domain.shared.domain_exceptions import ConflictError, NotFoundError
from src.shared.utils.hashing_utils import Hasher


class GroupRepository:
    @staticmethod
    def create(group: GroupCreate, db_session: Session) -> Group:
        new_group = Group(**group.model_dump(exclude_unset=True))
        new_group.link_url = Hasher.generate_group_token()
        try:
            db_session.add(new_group)
            db_session.flush()
            db_session.refresh(new_group)
        except IntegrityError:
            db_session.rollback()
            raise ConflictError("Group creation failed. Unique constraint violated.")
        return new_group

    @staticmethod
    def get_all(db_session: Session) -> list[Group]:
        stmt = select(Group)
        return list(db_session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_id(group_id: int, db_session: Session) -> Group:
        group = db_session.get(Group, group_id)
        if not group:
            raise NotFoundError("Group not found")
        return group

    @staticmethod
    def get_by_link_url(link_url: str, db_session: Session) -> Group:
        stmt = select(Group).where(Group.link_url == link_url)
        group = db_session.execute(stmt).scalars().one_or_none()
        if not group:
            raise NotFoundError("Group not found")
        return group
```

- [ ] **Step 4: Create `src/domain/group/group_service.py`**

```python
from sqlalchemy.orm import Session

from src.domain.group.group_repository import GroupRepository
from src.domain.group.group_schemas import GroupCreate, GroupList, GroupRead


class GroupService:
    @staticmethod
    def create(group: GroupCreate, db_session: Session) -> GroupRead:
        result = GroupRepository.create(group=group, db_session=db_session)
        return GroupRead.model_validate(result)

    @staticmethod
    def get_all(db_session: Session) -> GroupList:
        groups = GroupRepository.get_all(db_session=db_session)
        items = [GroupRead.model_validate(g) for g in groups]
        return GroupList(groups=items)

    @staticmethod
    def get_by_id(group_id: int, db_session: Session) -> GroupRead:
        result = GroupRepository.get_by_id(group_id=group_id, db_session=db_session)
        return GroupRead.model_validate(result)

    @staticmethod
    def get_by_link_url(link_url: str, db_session: Session) -> GroupRead:
        result = GroupRepository.get_by_link_url(link_url=link_url, db_session=db_session)
        return GroupRead.model_validate(result)
```

- [ ] **Step 5: Commit**

```bash
git add src/domain/group/
git commit -m "feat: migrate group domain context with SA 2.0 + Pydantic v2 upgrades"
```

---

## Task 4: Migrate participant domain context

**Files:**
- Create: `src/domain/participant/participant_schemas.py`
- Create: `src/domain/participant/participant_model.py`
- Create: `src/domain/participant/participant_repository.py`
- Create: `src/domain/participant/participant_service.py`

- [ ] **Step 1: Create `src/domain/participant/participant_schemas.py`**

```python
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator


class ParticipantStatus(str, Enum):
    PENDING = "PENDING"
    REVEALED = "REVEALED"


class ParticipantBase(BaseModel):
    """Minimal schema used by GroupRead to avoid circular imports."""
    model_config = {"from_attributes": True}

    id: int
    name: str


class ParticipantCreate(BaseModel):
    name: str
    group_id: int


class ParticipantRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    group_id: int
    gift_hint: Optional[str] = None
    status: ParticipantStatus = ParticipantStatus.PENDING
    created_at: datetime
    updated_at: Optional[datetime] = None


class ParticipantList(BaseModel):
    model_config = {"from_attributes": True}

    participants: list[ParticipantRead]


class ParticipantUpdate(BaseModel):
    name: Optional[str] = None
    gift_hint: Optional[str] = None
    status: Optional[ParticipantStatus] = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field(cls, values: dict) -> dict:
        if not values:
            raise ValueError("At least one field must be provided for update.")
        return values
```

- [ ] **Step 2: Create `src/domain/participant/participant_model.py`**

```python
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.shared.database_base import Base
from src.domain.participant.participant_schemas import ParticipantStatus


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    gift_hint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[ParticipantStatus] = mapped_column(
        SQLAlchemyEnum(ParticipantStatus), nullable=False, default=ParticipantStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, onupdate=lambda: datetime.now(timezone.utc)
    )

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    group: Mapped["Group"] = relationship(back_populates="participants")

    gift_giver: Mapped[Optional["SecretFriend"]] = relationship(
        foreign_keys="SecretFriend.gift_giver_id",
        back_populates="giver",
        uselist=False,
        cascade="all, delete-orphan",
    )
    gift_receiver: Mapped[Optional["SecretFriend"]] = relationship(
        foreign_keys="SecretFriend.gift_receiver_id",
        back_populates="receiver",
        uselist=False,
        cascade="all, delete-orphan",
    )
```

- [ ] **Step 3: Create `src/domain/participant/participant_repository.py`**

```python
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from src.domain.group.group_model import Group
from src.domain.participant.participant_model import Participant
from src.domain.participant.participant_schemas import ParticipantCreate, ParticipantUpdate
from src.domain.secret_friend.secret_friend_model import SecretFriend
from src.domain.shared.domain_exceptions import ConflictError, NotFoundError


class ParticipantRepository:
    @staticmethod
    def create(participant: ParticipantCreate, db_session: Session) -> Participant:
        group = db_session.get(Group, participant.group_id)
        if not group:
            raise NotFoundError("Group not found")

        new_participant = Participant(**participant.model_dump())
        try:
            db_session.add(new_participant)
            db_session.flush()
            db_session.refresh(new_participant)
        except IntegrityError:
            db_session.rollback()
            raise ConflictError("Participant creation failed. Unique constraint violated.")
        return new_participant

    @staticmethod
    def get_all(db_session: Session) -> list[Participant]:
        stmt = (
            select(Participant)
            .options(joinedload(Participant.gift_giver).joinedload(SecretFriend.receiver))
        )
        return list(db_session.execute(stmt).scalars().unique().all())

    @staticmethod
    def get_by_group_id(group_id: int, db_session: Session) -> list[Participant]:
        stmt = select(Participant).where(Participant.group_id == group_id)
        return list(db_session.execute(stmt).scalars().all())

    @staticmethod
    def get_by_id(participant_id: int, db_session: Session) -> Participant:
        stmt = (
            select(Participant)
            .options(joinedload(Participant.gift_giver).joinedload(SecretFriend.receiver))
            .where(Participant.id == participant_id)
        )
        participant = db_session.execute(stmt).scalars().unique().one_or_none()
        if not participant:
            raise NotFoundError("Participant not found")
        return participant

    @staticmethod
    def update(
        participant_id: int, payload: ParticipantUpdate, db_session: Session
    ) -> Participant:
        participant = db_session.get(Participant, participant_id)
        if not participant:
            raise NotFoundError("Participant not found")

        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(participant, key, value)

        try:
            db_session.flush()
            db_session.refresh(participant)
        except IntegrityError:
            db_session.rollback()
            raise ConflictError("Participant update failed. Unique constraint violated.")
        return participant
```

- [ ] **Step 4: Create `src/domain/participant/participant_service.py`**

```python
from sqlalchemy.orm import Session

from src.domain.participant.participant_repository import ParticipantRepository
from src.domain.participant.participant_schemas import (
    ParticipantCreate,
    ParticipantList,
    ParticipantRead,
    ParticipantUpdate,
)


class ParticipantService:
    @staticmethod
    def create(participant: ParticipantCreate, db_session: Session) -> ParticipantRead:
        result = ParticipantRepository.create(participant=participant, db_session=db_session)
        return ParticipantRead.model_validate(result)

    @staticmethod
    def get_all(db_session: Session) -> ParticipantList:
        participants = ParticipantRepository.get_all(db_session=db_session)
        items = [ParticipantRead.model_validate(p) for p in participants]
        return ParticipantList(participants=items)

    @staticmethod
    def get_by_group_id(group_id: int, db_session: Session) -> list[ParticipantRead]:
        participants = ParticipantRepository.get_by_group_id(
            group_id=group_id, db_session=db_session
        )
        return [ParticipantRead.model_validate(p) for p in participants]

    @staticmethod
    def get_by_id(participant_id: int, db_session: Session) -> ParticipantRead:
        result = ParticipantRepository.get_by_id(
            participant_id=participant_id, db_session=db_session
        )
        return ParticipantRead.model_validate(result)

    @staticmethod
    def update(
        participant_id: int, payload: ParticipantUpdate, db_session: Session
    ) -> ParticipantRead:
        result = ParticipantRepository.update(
            participant_id=participant_id, payload=payload, db_session=db_session
        )
        return ParticipantRead.model_validate(result)
```

- [ ] **Step 5: Commit**

```bash
git add src/domain/participant/
git commit -m "feat: migrate participant domain context with SA 2.0 + Pydantic v2 upgrades"
```

---

## Task 5: Migrate secret_friend domain context

**Files:**
- Create: `src/domain/secret_friend/secret_friend_schemas.py`
- Create: `src/domain/secret_friend/secret_friend_model.py`
- Create: `src/domain/secret_friend/secret_friend_repository.py`
- Create: `src/domain/secret_friend/secret_friend_service.py`

- [ ] **Step 1: Create `src/domain/secret_friend/secret_friend_schemas.py`**

```python
from pydantic import BaseModel, Field, model_validator


class SecretFriendLink(BaseModel):
    gift_giver_id: int = Field(..., gt=0)
    gift_receiver_id: int = Field(..., gt=0)

    @model_validator(mode="before")
    @classmethod
    def validate_ids_are_distinct(cls, data):
        gift_giver_id = data.get("gift_giver_id")
        gift_receiver_id = data.get("gift_receiver_id")
        if gift_giver_id is not None and gift_giver_id == gift_receiver_id:
            raise ValueError("Gift giver and gift receiver cannot be the same person.")
        return data


class SecretFriendRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    gift_giver_id: int
    gift_receiver_id: int
```

- [ ] **Step 2: Create `src/domain/secret_friend/secret_friend_model.py`**

```python
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.shared.database_base import Base


class SecretFriend(Base):
    __tablename__ = "secret_friends"
    __table_args__ = (
        UniqueConstraint(
            "gift_giver_id", "gift_receiver_id", name="uq_gift_giver_receiver"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    gift_giver_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), nullable=False)
    giver: Mapped[Optional["Participant"]] = relationship(
        foreign_keys=[gift_giver_id],
        back_populates="gift_giver",
    )

    gift_receiver_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), nullable=False)
    receiver: Mapped[Optional["Participant"]] = relationship(
        foreign_keys=[gift_receiver_id],
        back_populates="gift_receiver",
    )
```

- [ ] **Step 3: Create `src/domain/secret_friend/secret_friend_repository.py`**

```python
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.secret_friend.secret_friend_model import SecretFriend
from src.domain.secret_friend.secret_friend_schemas import SecretFriendLink
from src.domain.shared.domain_exceptions import ConflictError


class SecretFriendRepository:
    @staticmethod
    def link(secret_friend: SecretFriendLink, db_session: Session) -> SecretFriend:
        """Creates or updates a secret friend link (upsert by gift_giver_id)."""
        stmt = select(SecretFriend).where(
            SecretFriend.gift_giver_id == secret_friend.gift_giver_id
        )
        existing = db_session.execute(stmt).scalars().one_or_none()

        if existing:
            existing.gift_receiver_id = secret_friend.gift_receiver_id
            try:
                db_session.flush()
                db_session.refresh(existing)
            except IntegrityError:
                db_session.rollback()
                raise ConflictError("Secret friend link update failed.")
            return existing

        new_sf = SecretFriend(**secret_friend.model_dump())
        try:
            db_session.add(new_sf)
            db_session.flush()
            db_session.refresh(new_sf)
        except IntegrityError:
            db_session.rollback()
            raise ConflictError("Secret friend link failed. Unique constraint violated.")
        return new_sf
```

- [ ] **Step 4: Create `src/domain/secret_friend/secret_friend_service.py`**

```python
import random

from sqlalchemy.orm import Session

from src.domain.participant.participant_schemas import ParticipantRead
from src.domain.secret_friend.secret_friend_repository import SecretFriendRepository
from src.domain.secret_friend.secret_friend_schemas import SecretFriendLink, SecretFriendRead


class SecretFriendService:
    @staticmethod
    def sort_secret_friends(
        participant: ParticipantRead, participants: list[ParticipantRead]
    ) -> SecretFriendLink:
        """Shuffles participants and assigns a secret friend avoiding self-linking."""
        if len(participants) < 2:
            raise ValueError("At least 2 participants are required to assign secret friends.")
        random.shuffle(participants)

        for receiver in participants[1:] + [participants[0]]:
            if receiver.id == participant.id:
                continue
            return SecretFriendLink(
                gift_giver_id=participant.id, gift_receiver_id=receiver.id
            )
        raise ValueError("Unable to assign a secret friend for the participant.")

    @staticmethod
    def link(secret_friend: SecretFriendLink, db_session: Session) -> SecretFriendRead:
        result = SecretFriendRepository.link(
            secret_friend=secret_friend, db_session=db_session
        )
        return SecretFriendRead.model_validate(result)
```

- [ ] **Step 5: Commit**

```bash
git add src/domain/secret_friend/
git commit -m "feat: migrate secret_friend domain context with SA 2.0 + Pydantic v2 upgrades"
```

---

## Task 6: Create API layer (routes, middleware, router, dependencies)

**Files:**
- Create: `src/api/api_error_schemas.py`
- Create: `src/api/api_middleware.py`
- Create: `src/api/api_dependencies.py`
- Create: `src/api/group/group_routes.py`
- Create: `src/api/participant/participant_routes.py`
- Create: `src/api/secret_friend/secret_friend_routes.py`
- Create: `src/api/api_router.py`

- [ ] **Step 1: Create `src/api/api_error_schemas.py`**

```python
from typing import Optional

from pydantic import BaseModel


class ErrorMessage(BaseModel):
    msg: str


class ErrorResponse(BaseModel):
    detail: Optional[list[ErrorMessage]] = None
```

- [ ] **Step 2: Create `src/api/api_middleware.py`**

```python
import logging
import time

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

log = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path_template = request.url.path
        try:
            start = time.perf_counter()
            response = await call_next(request)
            elapsed_time = time.perf_counter() - start
            log.debug(f"server.call.elapsed.{path_template}: {elapsed_time}")
        except Exception as e:
            log.error(f"server.call.exception.{path_template}: {e}")
            raise e
        return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> StreamingResponse:
        try:
            return await call_next(request)
        except ValidationError as e:
            log.exception(e)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={"detail": e.errors()},
            )
        except ValueError as e:
            log.exception(e)
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": [
                        {"msg": "Invalid value.", "loc": ["unknown"], "type": "value_error"}
                    ]
                },
            )
        except Exception as e:
            log.exception(e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": [
                        {"msg": "Unexpected error.", "loc": ["unknown"], "type": "unknown_error"}
                    ]
                },
            )
```

- [ ] **Step 3: Create `src/api/api_dependencies.py`**

```python
from src.domain.shared.database_session import get_db

# Re-export get_db for convenience — routes import from here
__all__ = ["get_db"]
```

- [ ] **Step 4: Create `src/api/group/group_routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.domain.group.group_schemas import GroupCreate, GroupList, GroupRead
from src.domain.group.group_service import GroupService
from src.domain.shared.database_session import get_db
from src.domain.shared.database_transaction import transaction
from src.domain.shared.domain_exceptions import ConflictError, NotFoundError

router = APIRouter()


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
def create_group(group: GroupCreate, db_session: Session = Depends(get_db)):
    try:
        with transaction(db_session):
            return GroupService.create(group=group, db_session=db_session)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=GroupList)
def list_groups(db_session: Session = Depends(get_db)):
    return GroupService.get_all(db_session=db_session)


@router.get("/{group_id}", response_model=GroupRead)
def get_group(group_id: int, db_session: Session = Depends(get_db)):
    try:
        return GroupService.get_by_id(group_id=group_id, db_session=db_session)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/link/{link_url}", response_model=GroupRead)
def get_group_by_link(link_url: str, db_session: Session = Depends(get_db)):
    try:
        return GroupService.get_by_link_url(link_url=link_url, db_session=db_session)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

- [ ] **Step 5: Create `src/api/participant/participant_routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.domain.participant.participant_schemas import (
    ParticipantCreate,
    ParticipantList,
    ParticipantRead,
    ParticipantUpdate,
)
from src.domain.participant.participant_service import ParticipantService
from src.domain.shared.database_session import get_db
from src.domain.shared.database_transaction import transaction
from src.domain.shared.domain_exceptions import ConflictError, NotFoundError

router = APIRouter()


@router.post("", response_model=ParticipantRead, status_code=status.HTTP_201_CREATED)
def create_participant(
    participant: ParticipantCreate, db_session: Session = Depends(get_db)
):
    try:
        with transaction(db_session):
            return ParticipantService.create(participant=participant, db_session=db_session)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=ParticipantList)
def list_participants(db_session: Session = Depends(get_db)):
    return ParticipantService.get_all(db_session=db_session)


@router.get("/{participant_id}", response_model=ParticipantRead)
def get_participant(participant_id: int, db_session: Session = Depends(get_db)):
    try:
        return ParticipantService.get_by_id(
            participant_id=participant_id, db_session=db_session
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{participant_id}", response_model=ParticipantRead)
def update_participant(
    participant_id: int,
    payload: ParticipantUpdate,
    db_session: Session = Depends(get_db),
):
    try:
        with transaction(db_session):
            return ParticipantService.update(
                participant_id=participant_id, payload=payload, db_session=db_session
            )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
```

- [ ] **Step 6: Create `src/api/secret_friend/secret_friend_routes.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.domain.participant.participant_schemas import ParticipantStatus, ParticipantUpdate
from src.domain.participant.participant_service import ParticipantService
from src.domain.secret_friend.secret_friend_schemas import SecretFriendLink
from src.domain.secret_friend.secret_friend_service import SecretFriendService
from src.domain.shared.database_session import get_db
from src.domain.shared.database_transaction import transaction
from src.domain.shared.domain_exceptions import ConflictError, NotFoundError

router = APIRouter()


@router.get("/{group_id}/{participant_id}")
def generate_secret_friends(
    group_id: int, participant_id: int, db_session: Session = Depends(get_db)
):
    try:
        participant = ParticipantService.get_by_id(
            participant_id=participant_id, db_session=db_session
        )
        all_participants = ParticipantService.get_by_group_id(
            group_id=group_id, db_session=db_session
        )

        secret_friend_link = SecretFriendService.sort_secret_friends(
            participant=participant, participants=all_participants
        )

        with transaction(db_session):
            ParticipantService.update(
                participant_id=participant_id,
                payload=ParticipantUpdate(status=ParticipantStatus.REVEALED),
                db_session=db_session,
            )
            SecretFriendService.link(
                secret_friend=SecretFriendLink(
                    gift_giver_id=participant_id,
                    gift_receiver_id=secret_friend_link.gift_receiver_id,
                ),
                db_session=db_session,
            )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"secret_friends": secret_friend_link}
```

- [ ] **Step 7: Create `src/api/api_router.py`**

```python
from fastapi import APIRouter
from starlette.responses import JSONResponse

from src.api.api_error_schemas import ErrorResponse
from src.api.group.group_routes import router as group_router
from src.api.participant.participant_routes import router as participant_router
from src.api.secret_friend.secret_friend_routes import router as secret_friend_router

api_router = APIRouter(
    default_response_class=JSONResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)

api_router.include_router(group_router, prefix="/groups", tags=["groups"])
api_router.include_router(participant_router, prefix="/participants", tags=["participants"])
api_router.include_router(
    secret_friend_router, prefix="/secret-friends", tags=["secret-friends"]
)


@api_router.get("/healthcheck", include_in_schema=False)
def healthcheck():
    return {"status": "ok"}
```

- [ ] **Step 8: Commit**

```bash
git add src/api/
git commit -m "feat: create API layer with routes, middleware, router, error schemas"
```

---

## Task 7: Create app entry point and update external references

**Files:**
- Create: `src/app_main.py`
- Modify: `bin/run.py`
- Modify: `alembic/env.py`
- Modify: `docker/Dockerfile`

- [ ] **Step 1: Create `src/app_main.py`**

```python
import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sentry_asgi import SentryMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request

from src.api.api_middleware import ExceptionMiddleware, MetricsMiddleware
from src.api.api_router import api_router
from src.domain.shared.database_base import Base
from src.domain.shared.database_session import engine
from src.shared.rate_limiter_config import limiter

log = logging.getLogger(__name__)

# Application Setup
exception_handlers = {
    404: lambda request, exc: JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": [{"msg": "Not Found."}]},
    )
}

# Initialize main app
app = FastAPI(exception_handlers=exception_handlers, openapi_url="")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Initialize API app
api = FastAPI(
    title="Secret Friend Generator",
    description="Welcome to Secret Friend Generator's API documentation!",
    root_path="/api/v1",
)
api.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000 ; includeSubDomains"
    return response


# Add Middleware to API
api.add_middleware(SentryMiddleware)
api.add_middleware(MetricsMiddleware)
api.add_middleware(ExceptionMiddleware)

api.include_router(api_router)

# Mount API to main app
app.mount("/api/v1", app=api)


def create_tables():
    """Creates database tables if they do not exist. Use only for development."""
    Base.metadata.create_all(bind=engine)


def include_routers(app_instance: FastAPI):
    app_instance.include_router(api_router)


def start_application() -> FastAPI:
    create_tables()
    include_routers(app)
    return app


app = start_application()
```

- [ ] **Step 2: Update `bin/run.py`**

Replace `src.app.main:app` with `src.app_main:app` in both dev and prod commands:

```python
import os
from subprocess import run


def start():
    workers = os.getenv("WORKERS", "4")
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    environment = os.getenv("ENV", "development")

    if environment.lower() == "development":
        command = [
            "uvicorn",
            "src.app_main:app",
            "--host", host,
            "--port", port,
            "--reload",
        ]
    else:
        command = [
            "gunicorn",
            "-w", workers,
            "-k", "uvicorn.workers.UvicornWorker",
            "-b", f"{host}:{port}",
            "src.app_main:app",
        ]

    try:
        print(f"Starting server on {host}:{port} ({'Development' if environment.lower() == 'development' else 'Production'})...")
        run(command, check=True)
    except Exception as e:
        print(f"Failed to start the server: {e}")
        exit(1)
```

- [ ] **Step 3: Update `alembic/env.py`**

Replace imports:

```python
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from src.shared.app_config import settings
from src.domain.shared.database_base import Base

# Import all models so Alembic can detect them
from src.domain.group.group_model import Group  # noqa: F401
from src.domain.participant.participant_model import Participant  # noqa: F401
from src.domain.secret_friend.secret_friend_model import SecretFriend  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Update `docker/Dockerfile`**

Change CMD to use new entry point:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "src.app_main:app"]
```

- [ ] **Step 5: Commit**

```bash
git add src/app_main.py bin/run.py alembic/env.py docker/Dockerfile
git commit -m "feat: create app entry point and update all external references"
```

---

## Task 8: Set up test fixtures and update existing tests

**Files:**
- Modify: `tests/conftest.py`
- Create: `tests/domain/__init__.py`
- Create: `tests/domain/group/__init__.py`
- Create: `tests/domain/participant/__init__.py`
- Create: `tests/domain/secret_friend/__init__.py`
- Create: `tests/api/__init__.py`
- Create: `tests/api/group/__init__.py`
- Create: `tests/api/participant/__init__.py`
- Create: `tests/api/secret_friend/__init__.py`

- [ ] **Step 1: Create test directory `__init__.py` files**

```bash
mkdir -p tests/domain/group tests/domain/participant tests/domain/secret_friend
mkdir -p tests/api/group tests/api/participant tests/api/secret_friend
touch tests/domain/__init__.py tests/domain/group/__init__.py
touch tests/domain/participant/__init__.py tests/domain/secret_friend/__init__.py
touch tests/api/__init__.py tests/api/group/__init__.py
touch tests/api/participant/__init__.py tests/api/secret_friend/__init__.py
```

- [ ] **Step 2: Write `tests/conftest.py`**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from src.domain.shared.database_base import Base
from src.domain.shared.database_session import get_db
from src.domain.group.group_repository import GroupRepository
from src.domain.group.group_schemas import GroupCreate
from src.domain.participant.participant_repository import ParticipantRepository
from src.domain.participant.participant_schemas import ParticipantCreate

# Import models so Base.metadata knows all tables
from src.domain.group.group_model import Group  # noqa: F401
from src.domain.participant.participant_model import Participant  # noqa: F401
from src.domain.secret_friend.secret_friend_model import SecretFriend  # noqa: F401

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    _engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    """Each test runs in a transaction that is rolled back on teardown."""
    connection = engine.connect()
    txn = connection.begin()
    session = Session(connection)
    yield session
    session.close()
    txn.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session):
    """FastAPI test client with overridden db dependency."""
    from src.app_main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def group_fixture(db_session: Session):
    def _create(**overrides):
        defaults = {"name": "Test Group", "description": "A test group"}
        return GroupRepository.create(
            GroupCreate(**{**defaults, **overrides}), db_session
        )
    return _create


@pytest.fixture
def participant_fixture(db_session: Session, group_fixture):
    def _create(group=None, **overrides):
        group = group or group_fixture()
        defaults = {"name": "Test Participant", "group_id": group.id}
        return ParticipantRepository.create(
            ParticipantCreate(**{**defaults, **overrides}), db_session
        )
    return _create
```

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "feat: set up test fixtures with factory pattern and transaction rollback"
```

---

## Task 9: Delete old `src/app/` directory and verify

**Files:**
- Delete: `src/app/` (entire directory)

- [ ] **Step 1: Verify new structure works by running a quick import check**

```bash
python -c "from src.domain.shared.database_base import Base; from src.domain.group.group_model import Group; from src.domain.participant.participant_model import Participant; from src.domain.secret_friend.secret_friend_model import SecretFriend; print('All domain imports OK')"
```

Expected: `All domain imports OK`

- [ ] **Step 2: Verify API imports**

```bash
python -c "from src.api.api_router import api_router; print('API imports OK')"
```

Expected: `API imports OK`

- [ ] **Step 3: Delete old directory**

```bash
rm -rf src/app/
```

- [ ] **Step 4: Run linter to check for broken imports**

```bash
ruff check src/ --select F401,E402
```

Expected: No errors (or only expected `noqa` lines)

- [ ] **Step 5: Run tests**

```bash
pytest tests/ -v
```

Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor: remove old src/app/ directory, migration complete"
```

---

## Task 10: Final verification and cleanup

- [ ] **Step 1: Verify the app starts**

```bash
ENV=development python -c "from src.app_main import app; print(f'App created: {app.title}')"
```

Expected: `App created: Secret Friend Generator` (or similar — no import errors)

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass

- [ ] **Step 3: Verify success criteria checklist**

Manually check:
- [ ] All imports use absolute paths from `src.`
- [ ] No circular imports between layers
- [ ] `api/` never imports from `{ctx}_model.py` — only `{ctx}_schemas.py` and `{ctx}_service.py`
- [ ] All timestamps use `datetime.now(timezone.utc)`
- [ ] All SA models use `Mapped` + `mapped_column`
- [ ] All repos use `select()` instead of `session.query()`
- [ ] All repos use `flush()` instead of `commit()`
- [ ] Domain exceptions used instead of `ValueError`
- [ ] `domain_validators.py` exists with reusable validators

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: address final verification issues"
```
