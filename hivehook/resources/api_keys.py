from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import APIKey, APIKeyWithSecret, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_APIKEY_FIELDS = """
    id name keyPrefix scopes sourceIds
    createdAt expiresAt revokedAt lastUsedAt
"""

_LIST_QUERY = """
query ListAPIKeys($search: String, $limit: Int, $offset: Int) {
  apiKeys(search: $search, limit: $limit, offset: $offset) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _APIKEY_FIELDS

_GET_QUERY = """
query GetAPIKey($id: UUID!) {
  apiKey(id: $id) { %s }
}
""" % _APIKEY_FIELDS

_CREATE_MUTATION = """
mutation CreateAPIKey($input: CreateAPIKeyInput!) {
  createAPIKey(input: $input) {
    apiKey { %s }
    rawKey
  }
}
""" % _APIKEY_FIELDS

_REVOKE_MUTATION = """
mutation RevokeAPIKey($id: UUID!) {
  revokeAPIKey(id: $id)
}
"""


def _parse_api_key(data: dict[str, Any]) -> APIKey:
    return APIKey(
        id=data.get("id", ""),
        name=data.get("name", ""),
        key_prefix=data.get("keyPrefix", ""),
        scopes=data.get("scopes", []),
        source_ids=data.get("sourceIds", []),
        created_at=data.get("createdAt", ""),
        expires_at=data.get("expiresAt"),
        revoked_at=data.get("revokedAt"),
        last_used_at=data.get("lastUsedAt"),
    )


class APIKeyService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
    ) -> ListResult[APIKey]:
        v = build_list_vars(limit=limit, offset=offset, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["apiKeys"]
        return ListResult(
            nodes=[_parse_api_key(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> APIKey | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        k = data.get("apiKey")
        return _parse_api_key(k) if k else None

    def create(
        self, name: str, scopes: list[str],
        source_ids: list[str] | None = None,
        expires_at: str | None = None,
    ) -> APIKeyWithSecret:
        inp: dict[str, Any] = {"name": name, "scopes": scopes}
        if source_ids is not None:
            inp["sourceIds"] = source_ids
        if expires_at is not None:
            inp["expiresAt"] = expires_at
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        result = data["createAPIKey"]
        return APIKeyWithSecret(
            api_key=_parse_api_key(result["apiKey"]),
            raw_key=result["rawKey"],
        )

    def revoke(self, id: str) -> bool:
        data = self._t.execute(_REVOKE_MUTATION, {"id": id})
        return data.get("revokeAPIKey", False)

    def iterate(self, **filters: Any) -> Iterator[APIKey]:
        return paginate(self.list, **filters)


class AsyncAPIKeyService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
    ) -> ListResult[APIKey]:
        v = build_list_vars(limit=limit, offset=offset, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["apiKeys"]
        return ListResult(
            nodes=[_parse_api_key(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> APIKey | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        k = data.get("apiKey")
        return _parse_api_key(k) if k else None

    async def create(
        self, name: str, scopes: list[str],
        source_ids: list[str] | None = None,
        expires_at: str | None = None,
    ) -> APIKeyWithSecret:
        inp: dict[str, Any] = {"name": name, "scopes": scopes}
        if source_ids is not None:
            inp["sourceIds"] = source_ids
        if expires_at is not None:
            inp["expiresAt"] = expires_at
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        result = data["createAPIKey"]
        return APIKeyWithSecret(
            api_key=_parse_api_key(result["apiKey"]),
            raw_key=result["rawKey"],
        )

    async def revoke(self, id: str) -> bool:
        data = await self._t.execute(_REVOKE_MUTATION, {"id": id})
        return data.get("revokeAPIKey", False)

    def iterate(self, **filters: Any) -> AsyncIterator[APIKey]:
        return paginate_async(self.list, **filters)
