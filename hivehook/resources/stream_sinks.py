from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import StreamSink, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_SINK_FIELDS = """
    id streamId name sinkType config batchSize flushInterval cursorSequence status lastFlushedAt createdAt
"""

_LIST_QUERY = """
query ListStreamSinks($streamId: UUID!, $status: SinkStatus, $search: String,
                      $limit: Int, $offset: Int, $after: String, $first: Int) {
  streamSinks(streamId: $streamId, status: $status, search: $search,
              limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _SINK_FIELDS

_GET_QUERY = """
query GetStreamSink($id: UUID!) {
  streamSink(id: $id) { %s }
}
""" % _SINK_FIELDS

_CREATE_MUTATION = """
mutation CreateStreamSink($input: CreateStreamSinkInput!) {
  createStreamSink(input: $input) { %s }
}
""" % _SINK_FIELDS

_UPDATE_MUTATION = """
mutation UpdateStreamSink($id: UUID!, $input: UpdateStreamSinkInput!) {
  updateStreamSink(id: $id, input: $input) { %s }
}
""" % _SINK_FIELDS

_DELETE_MUTATION = """
mutation DeleteStreamSink($id: UUID!) {
  deleteStreamSink(id: $id)
}
"""


def _parse_sink(data: dict[str, Any]) -> StreamSink:
    return StreamSink(
        id=data.get("id", ""),
        stream_id=data.get("streamId", ""),
        name=data.get("name", ""),
        sink_type=data.get("sinkType", ""),
        config=data.get("config") or {},
        batch_size=data.get("batchSize", 0),
        flush_interval=data.get("flushInterval", ""),
        cursor_sequence=data.get("cursorSequence", 0),
        status=data.get("status", ""),
        last_flushed_at=data.get("lastFlushedAt"),
        created_at=data.get("createdAt", ""),
    )


class StreamSinkService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self,
        stream_id: str,
        status: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
    ) -> ListResult[StreamSink]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            streamId=stream_id, status=status, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["streamSinks"]
        return ListResult(
            nodes=[_parse_sink(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> StreamSink | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("streamSink")
        return _parse_sink(s) if s else None

    def create(
        self, stream_id: str, name: str, sink_type: str,
        config: dict[str, Any],
        batch_size: int | None = None,
        flush_interval: str | None = None,
    ) -> StreamSink:
        inp: dict[str, Any] = {"streamId": stream_id, "name": name, "sinkType": sink_type, "config": config}
        if batch_size is not None:
            inp["batchSize"] = batch_size
        if flush_interval is not None:
            inp["flushInterval"] = flush_interval
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_sink(data["createStreamSink"])

    def update(self, id: str, **kwargs: Any) -> StreamSink:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "config": "config", "batch_size": "batchSize",
                    "flush_interval": "flushInterval", "status": "status"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_sink(data["updateStreamSink"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteStreamSink", False)

    def iterate(self, stream_id: str, **filters: Any) -> Iterator[StreamSink]:
        return paginate(lambda **kw: self.list(stream_id, **kw), **filters)


class AsyncStreamSinkService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self,
        stream_id: str,
        status: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
    ) -> ListResult[StreamSink]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            streamId=stream_id, status=status, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["streamSinks"]
        return ListResult(
            nodes=[_parse_sink(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> StreamSink | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("streamSink")
        return _parse_sink(s) if s else None

    async def create(
        self, stream_id: str, name: str, sink_type: str,
        config: dict[str, Any],
        batch_size: int | None = None,
        flush_interval: str | None = None,
    ) -> StreamSink:
        inp: dict[str, Any] = {"streamId": stream_id, "name": name, "sinkType": sink_type, "config": config}
        if batch_size is not None:
            inp["batchSize"] = batch_size
        if flush_interval is not None:
            inp["flushInterval"] = flush_interval
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_sink(data["createStreamSink"])

    async def update(self, id: str, **kwargs: Any) -> StreamSink:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "config": "config", "batch_size": "batchSize",
                    "flush_interval": "flushInterval", "status": "status"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_sink(data["updateStreamSink"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteStreamSink", False)

    def iterate(self, stream_id: str, **filters: Any) -> AsyncIterator[StreamSink]:
        return paginate_async(lambda **kw: self.list(stream_id, **kw), **filters)
