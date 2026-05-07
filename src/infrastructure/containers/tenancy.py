"""Tenancy context container — UoW + use case providers for organizations.

Cross-cutting dependencies (event_publisher) are declared as
`providers.Dependency` and injected by the root container. This keeps the
sub-container free of imports from sibling containers.

The UoW is a Factory (not Singleton) so each request gets a fresh instance
built with its own per-request session.
"""

from dependency_injector import containers, providers

from src.contexts.tenancy.adapters.persistence.unit_of_work import (
    SQLAlchemyTenancyUnitOfWork,
)
from src.contexts.tenancy.use_cases.organization.add_member import AddMemberUseCase
from src.contexts.tenancy.use_cases.organization.change_role import (
    ChangeMemberRoleUseCase,
)
from src.contexts.tenancy.use_cases.organization.create import (
    CreateOrganizationUseCase,
)
from src.contexts.tenancy.use_cases.organization.list_my_organizations import (
    ListMyOrganizationsUseCase,
)
from src.contexts.tenancy.use_cases.organization.remove_member import (
    RemoveMemberUseCase,
)
from src.infrastructure.adapters.events.in_memory_publisher import (
    InMemoryEventPublisher,
)


class TenancyContainer(containers.DeclarativeContainer):
    event_publisher: providers.Dependency[InMemoryEventPublisher] = (
        providers.Dependency()
    )

    tenancy_uow = providers.Factory(SQLAlchemyTenancyUnitOfWork)

    create_organization_use_case = providers.Factory(
        CreateOrganizationUseCase,
        uow=tenancy_uow,
        event_publisher=event_publisher,
    )
    add_member_use_case = providers.Factory(
        AddMemberUseCase,
        uow=tenancy_uow,
        event_publisher=event_publisher,
    )
    remove_member_use_case = providers.Factory(
        RemoveMemberUseCase,
        uow=tenancy_uow,
        event_publisher=event_publisher,
    )
    change_member_role_use_case = providers.Factory(
        ChangeMemberRoleUseCase,
        uow=tenancy_uow,
        event_publisher=event_publisher,
    )
    list_my_organizations_use_case = providers.Factory(
        ListMyOrganizationsUseCase,
        uow=tenancy_uow,
    )
