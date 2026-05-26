from __future__ import annotations

from typing import Any

from hivehook.types import Source, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars

_SOURCE_FIELDS = """
    id name slug providerType
    verifyConfig status rateLimitRps spikeProtection maxIngestRps createdAt
"""

_LIST_QUERY = """
query ListSources($status: SourceStatus, $providerType: String, $search: String,
                   $limit: Int, $offset: Int, $after: String, $first: Int) {
  sources(status: $status, providerType: $providerType, search: $search,
          limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _SOURCE_FIELDS

_GET_QUERY = """
query GetSource($id: UUID!) {
  source(id: $id) { %s }
}
""" % _SOURCE_FIELDS

_CREATE_MUTATION = """
mutation CreateSource($input: CreateSourceInput!) {
  createSource(input: $input) { %s }
}
""" % _SOURCE_FIELDS

_UPDATE_MUTATION = """
mutation UpdateSource($id: UUID!, $input: UpdateSourceInput!) {
  updateSource(id: $id, input: $input) { %s }
}
""" % _SOURCE_FIELDS

_DELETE_MUTATION = """
mutation DeleteSource($id: UUID!) {
  deleteSource(id: $id)
}
"""

_ROTATE_SECRET_MUTATION = """
mutation RotateSourceSecret($id: UUID!) {
  rotateSourceSecret(id: $id) { %s }
}
""" % _SOURCE_FIELDS

_CLEAR_SECONDARY_MUTATION = """
mutation ClearSourceSecondarySecret($id: UUID!) {
  clearSourceSecondarySecret(id: $id) { %s }
}
""" % _SOURCE_FIELDS


def _parse_source(data: dict[str, Any]) -> Source:
    return Source(
        id=data.get("id", ""),
        name=data.get("name", ""),
        slug=data.get("slug", ""),
        provider_type=data.get("providerType", ""),
        verify_config=data.get("verifyConfig"),
        status=data.get("status", ""),
        rate_limit_rps=data.get("rateLimitRps", 0),
        spike_protection=data.get("spikeProtection", False),
        max_ingest_rps=data.get("maxIngestRps", 0),
        created_at=data.get("createdAt", ""),
    )


class SourceService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self,
        status: str | None = None,
        provider_type: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
    ) -> ListResult[Source]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            status=status, providerType=provider_type, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["sources"]
        return ListResult(
            nodes=[_parse_source(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Source | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("source")
        return _parse_source(s) if s else None

    def create(
        self, name: str, slug: str, provider_type: str,
        verify_config: dict[str, Any] | None = None,
        spike_protection: bool | None = None,
        max_ingest_rps: int | None = None,
    ) -> Source:
        inp: dict[str, Any] = {"name": name, "slug": slug, "providerType": provider_type}
        if verify_config is not None:
            inp["verifyConfig"] = verify_config
        if spike_protection is not None:
            inp["spikeProtection"] = spike_protection
        if max_ingest_rps is not None:
            inp["maxIngestRps"] = max_ingest_rps
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_source(data["createSource"])

    def update(self, id: str, **kwargs: Any) -> Source:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "slug": "slug", "status": "status",
                    "verify_config": "verifyConfig", "rate_limit_rps": "rateLimitRps",
                    "spike_protection": "spikeProtection", "max_ingest_rps": "maxIngestRps"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_source(data["updateSource"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteSource", False)

    def rotate_secret(self, id: str) -> Source:
        data = self._t.execute(_ROTATE_SECRET_MUTATION, {"id": id})
        return _parse_source(data["rotateSourceSecret"])

    def clear_secondary_secret(self, id: str) -> Source:
        data = self._t.execute(_CLEAR_SECONDARY_MUTATION, {"id": id})
        return _parse_source(data["clearSourceSecondarySecret"])


class AsyncSourceService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self,
        status: str | None = None,
        provider_type: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
    ) -> ListResult[Source]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            status=status, providerType=provider_type, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["sources"]
        return ListResult(
            nodes=[_parse_source(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Source | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("source")
        return _parse_source(s) if s else None

    async def create(
        self, name: str, slug: str, provider_type: str,
        verify_config: dict[str, Any] | None = None,
        spike_protection: bool | None = None,
        max_ingest_rps: int | None = None,
    ) -> Source:
        inp: dict[str, Any] = {"name": name, "slug": slug, "providerType": provider_type}
        if verify_config is not None:
            inp["verifyConfig"] = verify_config
        if spike_protection is not None:
            inp["spikeProtection"] = spike_protection
        if max_ingest_rps is not None:
            inp["maxIngestRps"] = max_ingest_rps
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_source(data["createSource"])

    async def update(self, id: str, **kwargs: Any) -> Source:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "slug": "slug", "status": "status",
                    "verify_config": "verifyConfig", "rate_limit_rps": "rateLimitRps",
                    "spike_protection": "spikeProtection", "max_ingest_rps": "maxIngestRps"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_source(data["updateSource"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteSource", False)

    async def rotate_secret(self, id: str) -> Source:
        data = await self._t.execute(_ROTATE_SECRET_MUTATION, {"id": id})
        return _parse_source(data["rotateSourceSecret"])

    async def clear_secondary_secret(self, id: str) -> Source:
        data = await self._t.execute(_CLEAR_SECONDARY_MUTATION, {"id": id})
        return _parse_source(data["clearSourceSecondarySecret"])
