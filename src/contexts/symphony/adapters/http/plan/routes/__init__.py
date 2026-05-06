"""Route registration — import all plan route modules so decorators fire."""

import src.contexts.symphony.adapters.http.plan.routes.create  # noqa: F401
import src.contexts.symphony.adapters.http.plan.routes.get  # noqa: F401
import src.contexts.symphony.adapters.http.plan.routes.list_for_run  # noqa: F401
import src.contexts.symphony.adapters.http.plan.routes.approve  # noqa: F401
import src.contexts.symphony.adapters.http.plan.routes.reject  # noqa: F401
