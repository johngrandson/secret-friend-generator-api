"""Route registration — import all spec route modules so decorators fire."""

import src.contexts.symphony.adapters.http.spec.routes.create  # noqa: F401
import src.contexts.symphony.adapters.http.spec.routes.get  # noqa: F401
import src.contexts.symphony.adapters.http.spec.routes.list_for_run  # noqa: F401
import src.contexts.symphony.adapters.http.spec.routes.approve  # noqa: F401
import src.contexts.symphony.adapters.http.spec.routes.reject  # noqa: F401
