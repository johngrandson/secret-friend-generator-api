"""Application root container — composes per-aggregate sub-containers.

To add a new bounded context, create `containers/<aggregate>.py` defining a
`DeclarativeContainer`, then expose it here as a `providers.Container(...)`,
forwarding any cross-cutting dependencies from `core`. The root holds the
wiring configuration so every adapter package is wired recursively.
"""

from dependency_injector import containers, providers

from src.infrastructure.containers.core import CoreContainer
from src.infrastructure.containers.user import UserContainer


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["src.adapters.http"],
    )

    core = providers.Container(CoreContainer)

    user = providers.Container(
        UserContainer,
        event_publisher=core.event_publisher,
    )
