from __future__ import annotations

import json
import time
from typing import Any

import requests

from hivehook.errors import (
    APIError,
    AuthError,
    ConflictError,
    HivehookError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class Transport:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        session: requests.Session | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._session = session or requests.Session()
        self._owns_session = session is None
        self._timeout = timeout
        self._max_retries = max_retries

    def execute(self, query: str, variables: dict[str, Any] | None = None) -> Any:
        from hivehook import __version__
        url = f"{self._base_url}/graphql"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"hivehook-python/{__version__}",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        attempt = 0
        while True:
            try:
                resp = self._session.post(
                    url, json=payload, headers=headers, timeout=self._timeout
                )
            except requests.ConnectionError as err:
                if attempt < self._max_retries:
                    sleep_for = _backoff(attempt)
                    time.sleep(sleep_for)
                    attempt += 1
                    continue
                raise HivehookError(f"network error: {err}", cause=err) from err
            except requests.RequestException as err:
                raise HivehookError(f"request failed: {err}", cause=err) from err

            try:
                body = resp.json()
            except (ValueError, json.JSONDecodeError):
                body = {"message": resp.text}

            header_retry_after = _parse_header_retry_after(resp.headers.get("Retry-After"))

            try:
                return self._handle_response(resp.status_code, body, header_retry_after)
            except (RateLimitError, ServerError) as err:
                if attempt < self._max_retries:
                    delay: float
                    if isinstance(err, RateLimitError) and err.retry_after is not None:
                        delay = err.retry_after
                    elif header_retry_after is not None:
                        delay = header_retry_after
                    else:
                        delay = _backoff(attempt)
                    time.sleep(delay)
                    attempt += 1
                    continue
                raise

    def close(self) -> None:
        if self._owns_session and self._session is not None:
            self._session.close()

    def _handle_response(
        self,
        status_code: int,
        body: Any,
        header_retry_after: float | None = None,
    ) -> Any:
        extensions = self._extract_extensions(body)

        if status_code == 401 or status_code == 403:
            msg = self._extract_error(body)
            raise AuthError(msg or "authentication failed", status_code, extensions=extensions)

        if status_code == 429:
            msg = self._extract_error(body)
            retry_after = _parse_retry_after(extensions)
            if retry_after is None:
                retry_after = header_retry_after
            raise RateLimitError(
                msg or "rate limited",
                status_code,
                extensions=extensions,
                retry_after=retry_after,
            )

        if 500 <= status_code < 600:
            msg = self._extract_error(body)
            raise ServerError(msg or f"server error {status_code}", status_code, extensions=extensions)

        if status_code >= 400:
            msg = self._extract_error(body)
            raise APIError(msg or f"HTTP {status_code}", status_code, extensions=extensions)

        if isinstance(body, dict) and "errors" in body and body["errors"]:
            err = body["errors"][0]
            msg = err.get("message", "unknown error")
            ext = err.get("extensions", {}) or {}
            code = ext.get("code", "")

            if code == "NOT_FOUND" or "not found" in msg.lower():
                raise NotFoundError(msg, extensions=ext)
            if code == "CONFLICT" or "conflict" in msg.lower() or "already exists" in msg.lower():
                raise ConflictError(msg, extensions=ext)
            if code == "VALIDATION" or "validation" in msg.lower():
                raise ValidationError(msg, extensions=ext)
            if code == "UNAUTHORIZED":
                raise AuthError(msg, extensions=ext)
            if code == "RATE_LIMITED":
                raise RateLimitError(msg, extensions=ext, retry_after=_parse_retry_after(ext))
            raise APIError(msg, extensions=ext)

        return body.get("data", {}) if isinstance(body, dict) else body

    def _extract_error(self, body: Any) -> str:
        if isinstance(body, dict):
            if "errors" in body and body["errors"]:
                return body["errors"][0].get("message", "")
            if "message" in body:
                return body["message"]
        return ""

    def _extract_extensions(self, body: Any) -> dict[str, Any] | None:
        if isinstance(body, dict) and body.get("errors"):
            err = body["errors"][0]
            ext = err.get("extensions")
            if isinstance(ext, dict):
                return ext
        return None


def _backoff(attempt: int) -> float:
    return min(2.0 ** attempt * 0.1, 5.0)


def _parse_retry_after(extensions: dict[str, Any] | None) -> float | None:
    if not extensions:
        return None
    val = extensions.get("retryAfter") or extensions.get("retry_after")
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _parse_header_retry_after(val: str | None) -> float | None:
    if not val:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
