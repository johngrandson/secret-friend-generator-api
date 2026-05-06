"""Route registration — import all run route modules so decorators fire."""

import src.contexts.symphony.adapters.http.run.routes.create  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.get  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.list  # noqa: F401
