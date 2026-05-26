from __future__ import annotations

from typing import Any


class HivehookError(Exception):
    def __init__(self, message: str, cause: BaseException | None = None):
        self.message = message
        self.cause = cause
        super().__init__(message)


class APIError(HivehookError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        extensions: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.extensions = extensions
        # Don't pass cause through to HivehookError, just store message
        super().__init__(message)


class NotFoundError(APIError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        extensions: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code, extensions)


class ConflictError(APIError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        extensions: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code, extensions)


class AuthError(APIError):
    def __init__(
        self,
        message: str,
        status_code: int = 401,
        extensions: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code, extensions)


class ValidationError(APIError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        extensions: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code, extensions)


class RateLimitError(APIError):
    def __init__(
        self,
        message: str,
        status_code: int = 429,
        extensions: dict[str, Any] | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message, status_code, extensions)
        self.retry_after = retry_after


class ServerError(APIError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        extensions: dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code, extensions)
