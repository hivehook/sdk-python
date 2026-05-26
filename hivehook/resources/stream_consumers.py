from __future__ import annotations

from typing import Any

from hivehook.types import StreamConsumer, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars

_CONSUMER_FIELDS = """
    id streamId name cursorSequence createdAt updatedAt
"""

_LIST_QUERY = """
query ListStreamConsumers($streamId: UUID!, $search: String,
                          $limit: Int, $offset: Int, $after: String, $first: Int) {
  streamConsumers(streamId: $streamId, search: $search,
                  limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _CONSUMER_FIELDS

_GET_QUERY = """
query GetStreamConsumer($id: UUID!) {
  streamConsumer(id: $id) { %s }
}
""" % _CONSUMER_FIELDS

_CREATE_MUTATION = """
mutation CreateStreamConsumer($input: CreateStreamConsumerInput!) {
  createStreamConsumer(input: $input) { %s }
}
""" % _CONSUMER_FIELDS

_DELETE_MUTATION = """
mutation DeleteStreamConsumer($id: UUID!) {
  deleteStreamConsumer(id: $id)
}
"""

_ADVANCE_CURSOR_MUTATION = """
mutation AdvanceConsumerCursor($id: UUID!, $sequence: Int!) {
  advanceConsumerCursor(id: $id, sequence: $sequence) { %s }
}
""" % _CONSUMER_FIELDS


def _parse_consumer(data: dict[str, Any]) -> StreamConsumer:
    return StreamConsumer(
        id=data.get("id", ""),
        stream_id=data.get("streamId", ""),
        name=data.get("name", ""),
        cursor_sequence=data.get("cursorSequence", 0),
        created_at=data.get("createdAt", ""),
        updated_at=data.get("updatedAt", ""),
    )


class StreamConsumerService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self,
        stream_id: str,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
    ) -> ListResult[StreamConsumer]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            streamId=stream_id, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["streamConsumers"]
        return ListResult(
            nodes=[_parse_consumer(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> StreamConsumer | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        c = data.get("streamConsumer")
        return _parse_consumer(c) if c else None

    def create(self, stream_id: str, name: str) -> StreamConsumer:
        inp = {"streamId": stream_id, "name": name}
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_consumer(data["createStreamConsumer"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteStreamConsumer", False)

    def advance_cursor(self, id: str, sequence: int) -> StreamConsumer:
        data = self._t.execute(_ADVANCE_CURSOR_MUTATION, {"id": id, "sequence": sequence})
        return _parse_consumer(data["advanceConsumerCursor"])


class AsyncStreamConsumerService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self,
        stream_id: str,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
    ) -> ListResult[StreamConsumer]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            streamId=stream_id, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["streamConsumers"]
        return ListResult(
            nodes=[_parse_consumer(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> StreamConsumer | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        c = data.get("streamConsumer")
        return _parse_consumer(c) if c else None

    async def create(self, stream_id: str, name: str) -> StreamConsumer:
        inp = {"streamId": stream_id, "name": name}
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_consumer(data["createStreamConsumer"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteStreamConsumer", False)

    async def advance_cursor(self, id: str, sequence: int) -> StreamConsumer:
        data = await self._t.execute(_ADVANCE_CURSOR_MUTATION, {"id": id, "sequence": sequence})
        return _parse_consumer(data["advanceConsumerCursor"])
