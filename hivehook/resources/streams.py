from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import Stream, StreamEntry, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_STREAM_FIELDS = """
    id applicationId name status retentionDays createdAt
"""

_LIST_QUERY = """
query ListStreams($applicationId: UUID, $status: StreamStatus, $search: String,
                  $limit: Int, $offset: Int, $after: String, $first: Int) {
  streams(applicationId: $applicationId, status: $status, search: $search,
          limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _STREAM_FIELDS

_GET_QUERY = """
query GetStream($id: UUID!) {
  stream(id: $id) { %s }
}
""" % _STREAM_FIELDS

_CREATE_MUTATION = """
mutation CreateStream($input: CreateStreamInput!) {
  createStream(input: $input) { %s }
}
""" % _STREAM_FIELDS

_UPDATE_MUTATION = """
mutation UpdateStream($id: UUID!, $input: UpdateStreamInput!) {
  updateStream(id: $id, input: $input) { %s }
}
""" % _STREAM_FIELDS

_DELETE_MUTATION = """
mutation DeleteStream($id: UUID!) {
  deleteStream(id: $id)
}
"""

_STREAM_ENTRY_FIELDS = "id streamId sequence messageId eventType payload createdAt"

_LIST_ENTRIES_QUERY = """
query ListStreamEntries($streamId: UUID!, $afterSequence: Int, $limit: Int) {
  streamEntries(streamId: $streamId, afterSequence: $afterSequence, limit: $limit) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _STREAM_ENTRY_FIELDS


def _parse_stream_entry(data: dict[str, Any]) -> StreamEntry:
    return StreamEntry(
        id=data.get("id", ""),
        stream_id=data.get("streamId", ""),
        sequence=data.get("sequence", 0),
        message_id=data.get("messageId"),
        event_type=data.get("eventType", ""),
        payload=data.get("payload", ""),
        created_at=data.get("createdAt", ""),
    )


def _parse_stream(data: dict[str, Any]) -> Stream:
    return Stream(
        id=data.get("id", ""),
        application_id=data.get("applicationId", ""),
        name=data.get("name", ""),
        status=data.get("status", ""),
        retention_days=data.get("retentionDays", 0),
        created_at=data.get("createdAt", ""),
    )


class StreamService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self,
        application_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
    ) -> ListResult[Stream]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            applicationId=application_id, status=status, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["streams"]
        return ListResult(
            nodes=[_parse_stream(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Stream | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("stream")
        return _parse_stream(s) if s else None

    def create(
        self, application_id: str, name: str,
        retention_days: int | None = None, status: str | None = None,
    ) -> Stream:
        inp: dict[str, Any] = {"applicationId": application_id, "name": name}
        if retention_days is not None:
            inp["retentionDays"] = retention_days
        if status is not None:
            inp["status"] = status
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_stream(data["createStream"])

    def update(self, id: str, **kwargs: Any) -> Stream:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "retention_days": "retentionDays", "status": "status"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_stream(data["updateStream"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteStream", False)

    def iterate(self, **filters: Any) -> Iterator[Stream]:
        return paginate(self.list, **filters)

    def entries(
        self, stream_id: str, after_sequence: int | None = None, limit: int | None = None,
    ) -> ListResult[StreamEntry]:
        v: dict[str, Any] = {"streamId": stream_id}
        if after_sequence is not None:
            v["afterSequence"] = after_sequence
        if limit is not None:
            v["limit"] = limit
        data = self._t.execute(_LIST_ENTRIES_QUERY, v)
        conn = data["streamEntries"]
        return ListResult(
            nodes=[_parse_stream_entry(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )


class AsyncStreamService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self,
        application_id: str | None = None,
        status: str | None = None,
        search: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        after: str | None = None,
        first: int | None = None,
    ) -> ListResult[Stream]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            applicationId=application_id, status=status, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["streams"]
        return ListResult(
            nodes=[_parse_stream(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Stream | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("stream")
        return _parse_stream(s) if s else None

    async def create(
        self, application_id: str, name: str,
        retention_days: int | None = None, status: str | None = None,
    ) -> Stream:
        inp: dict[str, Any] = {"applicationId": application_id, "name": name}
        if retention_days is not None:
            inp["retentionDays"] = retention_days
        if status is not None:
            inp["status"] = status
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_stream(data["createStream"])

    async def update(self, id: str, **kwargs: Any) -> Stream:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "retention_days": "retentionDays", "status": "status"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_stream(data["updateStream"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteStream", False)

    def iterate(self, **filters: Any) -> AsyncIterator[Stream]:
        return paginate_async(self.list, **filters)

    async def entries(
        self, stream_id: str, after_sequence: int | None = None, limit: int | None = None,
    ) -> ListResult[StreamEntry]:
        v: dict[str, Any] = {"streamId": stream_id}
        if after_sequence is not None:
            v["afterSequence"] = after_sequence
        if limit is not None:
            v["limit"] = limit
        data = await self._t.execute(_LIST_ENTRIES_QUERY, v)
        conn = data["streamEntries"]
        return ListResult(
            nodes=[_parse_stream_entry(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )
