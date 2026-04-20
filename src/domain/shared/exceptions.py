"""Domain exception hierarchy.

All domain exceptions inherit from DomainError. The ExceptionMiddleware
maps each subclass to an HTTP status code — routes never catch these.

DomainError (base)
├── NotFoundError     → 404
├── ConflictError     → 409
└── BusinessRuleError → 422
"""


class DomainError(Exception):
    """Base for all domain-layer exceptions."""


class NotFoundError(DomainError):
    """Requested resource does not exist."""


class ConflictError(DomainError):
    """Operation conflicts with current state (duplicate, etc.)."""


class BusinessRuleError(DomainError):
    """Domain invariant violated (e.g., not enough participants)."""
