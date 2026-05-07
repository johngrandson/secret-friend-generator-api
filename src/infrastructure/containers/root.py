"""Application root container — composes per-context sub-containers.

To add a new bounded context, create `containers/<context>.py` defining a
`DeclarativeContainer`, then expose it here as a `providers.Container(...)`,
forwarding any cross-cutting dependencies from `core`. The root holds the
wiring configuration so every adapter package is wired recursively.
"""

from dependency_injector import containers, providers

from src.infrastructure.containers.core import CoreContainer
from src.infrastructure.containers.identity import IdentityContainer
from src.infrastructure.containers.symphony import SymphonyContainer
from src.infrastructure.containers.tenancy import TenancyContainer


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=[
            "src.contexts.identity.adapters.http",
            "src.contexts.symphony.adapters.http",
            "src.contexts.tenancy.adapters.http",
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
        config=core.config,
    )

    tenancy = providers.Container(
        TenancyContainer,
        event_publisher=core.event_publisher,
    )
