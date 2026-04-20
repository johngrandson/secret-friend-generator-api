from typing import Optional

from pydantic import BaseModel


class ErrorMessage(BaseModel):
    msg: str


class ErrorResponse(BaseModel):
    detail: Optional[list[ErrorMessage]] = None
