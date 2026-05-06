"""User HTTP adapter package.

Pattern
-------
Each route file in `routes/` imports the shared `router` from `_router.py`
and registers exactly one endpoint via a decorator.  This `__init__` imports
`routes` (the sub-package) so that all decorator side-effects run, then
re-exports `router` for use in `main.py`.

    from src.adapters.http.user import router
    app.include_router(router)
"""

from src.adapters.http.user._router import router
import src.adapters.http.user.routes  # noqa: F401 — triggers route registration

__all__ = ["router"]
