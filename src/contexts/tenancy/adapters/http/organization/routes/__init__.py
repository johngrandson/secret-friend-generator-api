"""Side-effect imports register Organization route handlers on the shared router."""

import src.contexts.tenancy.adapters.http.organization.routes.add_member  # noqa: F401
import src.contexts.tenancy.adapters.http.organization.routes.change_role  # noqa: F401
import src.contexts.tenancy.adapters.http.organization.routes.create  # noqa: F401
import src.contexts.tenancy.adapters.http.organization.routes.list_my  # noqa: F401
import src.contexts.tenancy.adapters.http.organization.routes.remove_member  # noqa: F401
