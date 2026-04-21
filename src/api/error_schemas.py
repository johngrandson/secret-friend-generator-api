from pydantic import BaseModel


class ErrorMessage(BaseModel):
    msg: str


class ErrorResponse(BaseModel):
    detail: list[ErrorMessage] | None = None
