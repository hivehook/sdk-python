from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PortalToken:
    token: str
    expires_at: str


_GENERATE_TOKEN_MUTATION = """
mutation GeneratePortalToken($applicationId: UUID!) {
    generatePortalToken(applicationId: $applicationId) {
        token
        expiresAt
    }
}
"""


def _parse_portal_token(data: dict[str, Any]) -> PortalToken:
    return PortalToken(
        token=data["token"],
        expires_at=data["expiresAt"],
    )


class PortalService:
    def __init__(self, transport: Any) -> None:
        self._t = transport

    def generate_token(self, application_id: str) -> PortalToken:
        data = self._t.execute(_GENERATE_TOKEN_MUTATION, {"applicationId": application_id})
        return _parse_portal_token(data["generatePortalToken"])


class AsyncPortalService:
    def __init__(self, transport: Any) -> None:
        self._t = transport

    async def generate_token(self, application_id: str) -> PortalToken:
        data = await self._t.execute(_GENERATE_TOKEN_MUTATION, {"applicationId": application_id})
        return _parse_portal_token(data["generatePortalToken"])
