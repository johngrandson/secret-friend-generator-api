"""Model registry — importing this module ensures every aggregate's SQLAlchemy
model is registered on the shared ``Base.metadata``.

This is the ONLY place that should carry ``# noqa: F401`` for model side-effects.
Callers (database.py, alembic/env.py) just do:
    import src.infrastructure.adapters.persistence.registry

When adding a new aggregate, append one line here:

    import src.contexts.<context>.adapters.persistence.<aggregate>.model  # noqa: F401
"""

import src.contexts.identity.adapters.persistence.user.model  # noqa: F401 — registers UserModel
import src.contexts.symphony.adapters.persistence.run.model  # noqa: F401 — registers RunModel
import src.contexts.symphony.adapters.persistence.spec.model  # noqa: F401 — registers SpecModel
import src.contexts.symphony.adapters.persistence.plan.model  # noqa: F401 — registers PlanModel
