from __future__ import annotations

from typing import Any

from hivehook.types import Event, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars

_EVENT_FIELDS = """
    id sourceId idempotencyKey eventType
    headers rawBody status receivedAt
"""

_LIST_QUERY = """
query ListEvents($sourceId: UUID, $eventType: String, $status: EventStatus,
                  $search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  events(sourceId: $sourceId, eventType: $eventType, status: $status,
         search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _EVENT_FIELDS

_GET_QUERY = """
query GetEvent($id: UUID!) {
  event(id: $id) { %s }
}
""" % _EVENT_FIELDS


def _parse_event(data: dict[str, Any]) -> Event:
    return Event(
        id=data.get("id", ""),
        source_id=data.get("sourceId", ""),
        idempotency_key=data.get("idempotencyKey", ""),
        event_type=data.get("eventType", ""),
        headers=data.get("headers"),
        raw_body=data.get("rawBody"),
        status=data.get("status", ""),
        received_at=data.get("receivedAt", ""),
    )


class EventService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, source_id: str | None = None, event_type: str | None = None,
        status: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Event]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            sourceId=source_id, eventType=event_type,
                            status=status, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["events"]
        return ListResult(
            nodes=[_parse_event(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Event | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        e = data.get("event")
        return _parse_event(e) if e else None


class AsyncEventService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, source_id: str | None = None, event_type: str | None = None,
        status: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Event]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            sourceId=source_id, eventType=event_type,
                            status=status, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["events"]
        return ListResult(
            nodes=[_parse_event(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Event | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        e = data.get("event")
        return _parse_event(e) if e else None
