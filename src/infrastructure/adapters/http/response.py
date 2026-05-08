"""Shared HTTP response helpers for FastAPI route handlers.

Centralises the repeated ``if not resp.success`` / ``if payload is None``
guard that appears in every route handler across all bounded contexts.
"""

from typing import Protocol, TypeVar, overload

from fastapi import HTTPException, status

T = TypeVar("T")
_UNSET: object = object()


class _UseCaseResp(Protocol):
    """Minimal shape every use-case response satisfies (duck-typed)."""

    @property
    def success(self) -> bool: ...
    @property
    def error_message(self) -> str | None: ...


@overload
def raise_for_use_case_response(
    resp: _UseCaseResp,
    payload: T | None,
    *,
    default_status: int = ...,
    not_found_keyword: str = ...,
) -> T: ...


@overload
def raise_for_use_case_response(
    resp: _UseCaseResp,
    *,
    default_status: int = ...,
    not_found_keyword: str = ...,
) -> None: ...


def raise_for_use_case_response(
    resp: _UseCaseResp,
    payload: object = _UNSET,
    *,
    default_status: int = status.HTTP_400_BAD_REQUEST,
    not_found_keyword: str = "not found",
) -> object:
    """Raise or return narrowed payload.

    * ``not resp.success`` → 404 if *not_found_keyword* is in the error
      message (case-insensitive), *default_status* otherwise.
    * *payload* ``None`` → 500.
    * Returns *payload* (typed as ``T``) so callers can assign without cast.
    """
    if not resp.success:
        msg: str = resp.error_message or ""
        if not_found_keyword and not_found_keyword.lower() in msg.lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=msg or None)
        raise HTTPException(default_status, detail=msg or None)
    if payload is _UNSET:
        return None
    if payload is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error"
        )
    return payload
