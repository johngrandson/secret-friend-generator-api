"""Route registration — import all run route modules so decorators fire."""

import src.contexts.symphony.adapters.http.run.routes.create  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.dispatch  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.get  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.get_detail  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.get_latest_plan  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.get_latest_spec  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.list  # noqa: F401
import src.contexts.symphony.adapters.http.run.routes.orchestrate  # noqa: F401
