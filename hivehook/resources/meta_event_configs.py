from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import MetaEventConfig, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_FIELDS = "id name url signingSecret eventTypes enabled createdAt"

_LIST_QUERY = """
query ListMetaEventConfigs($search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  metaEventConfigs(search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _FIELDS

_GET_QUERY = """
query GetMetaEventConfig($id: UUID!) {
  metaEventConfig(id: $id) { %s }
}
""" % _FIELDS

_CREATE_MUTATION = """
mutation CreateMetaEventConfig($input: CreateMetaEventConfigInput!) {
  createMetaEventConfig(input: $input) { %s }
}
""" % _FIELDS

_UPDATE_MUTATION = """
mutation UpdateMetaEventConfig($id: UUID!, $input: UpdateMetaEventConfigInput!) {
  updateMetaEventConfig(id: $id, input: $input) { %s }
}
""" % _FIELDS

_DELETE_MUTATION = """
mutation DeleteMetaEventConfig($id: UUID!) {
  deleteMetaEventConfig(id: $id)
}
"""


def _parse(data: dict[str, Any]) -> MetaEventConfig:
    return MetaEventConfig(
        id=data.get("id", ""),
        name=data.get("name", ""),
        url=data.get("url", ""),
        signing_secret=data.get("signingSecret", ""),
        event_types=list(data.get("eventTypes") or []),
        enabled=data.get("enabled", True),
        created_at=data.get("createdAt", ""),
    )


def _build_input(name: str | None, url: str | None, event_types: list[str] | None, enabled: bool | None) -> dict[str, Any]:
    inp: dict[str, Any] = {}
    if name is not None:
        inp["name"] = name
    if url is not None:
        inp["url"] = url
    if event_types is not None:
        inp["eventTypes"] = event_types
    if enabled is not None:
        inp["enabled"] = enabled
    return inp


class MetaEventConfigService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[MetaEventConfig]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["metaEventConfigs"]
        return ListResult(
            nodes=[_parse(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> MetaEventConfig | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        r = data.get("metaEventConfig")
        return _parse(r) if r else None

    def create(self, name: str, url: str, event_types: list[str], enabled: bool | None = None) -> MetaEventConfig:
        inp = _build_input(name, url, event_types, enabled)
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse(data["createMetaEventConfig"])

    def update(
        self, id: str, name: str | None = None, url: str | None = None,
        event_types: list[str] | None = None, enabled: bool | None = None,
    ) -> MetaEventConfig:
        inp = _build_input(name, url, event_types, enabled)
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse(data["updateMetaEventConfig"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteMetaEventConfig", False)

    def iterate(self, **filters: Any) -> Iterator[MetaEventConfig]:
        return paginate(self.list, **filters)


class AsyncMetaEventConfigService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[MetaEventConfig]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["metaEventConfigs"]
        return ListResult(
            nodes=[_parse(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> MetaEventConfig | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        r = data.get("metaEventConfig")
        return _parse(r) if r else None

    async def create(self, name: str, url: str, event_types: list[str], enabled: bool | None = None) -> MetaEventConfig:
        inp = _build_input(name, url, event_types, enabled)
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse(data["createMetaEventConfig"])

    async def update(
        self, id: str, name: str | None = None, url: str | None = None,
        event_types: list[str] | None = None, enabled: bool | None = None,
    ) -> MetaEventConfig:
        inp = _build_input(name, url, event_types, enabled)
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse(data["updateMetaEventConfig"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteMetaEventConfig", False)

    def iterate(self, **filters: Any) -> AsyncIterator[MetaEventConfig]:
        return paginate_async(self.list, **filters)
