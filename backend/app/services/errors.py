from __future__ import annotations

from typing import Optional

from ..schemas.api import ErrorBody, ErrorEnvelope


class ApiError(Exception):
    """Raised by services; main.py turns it into an ErrorEnvelope response with `status`."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        stage: Optional[str] = None,
        retryable: bool = False,
        turn_id: Optional[int] = None,
    ):
        super().__init__(message)
        self.status = status
        self.body = ErrorBody(code=code, message=message, stage=stage, retryable=retryable, turn_id=turn_id)

    def envelope(self) -> dict:
        return ErrorEnvelope(error=self.body).model_dump()
