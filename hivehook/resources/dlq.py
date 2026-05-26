from __future__ import annotations

from typing import Any

from hivehook.types import DLQEntry, ListResult, ReplayResult, PurgeResult
from hivehook.resources._base import parse_page_info, build_list_vars

_DLQ_FIELDS = "id deliveryId eventId lastError replayedAt createdAt"

_LIST_QUERY = """
query ListDLQEntries($eventId: UUID, $replayed: Boolean, $search: String,
                      $limit: Int, $offset: Int, $after: String, $first: Int) {
  dlqEntries(eventId: $eventId, replayed: $replayed, search: $search,
             limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _DLQ_FIELDS

_REPLAY_MUTATION = """
mutation ReplayDLQEntry($id: UUID!) {
  replayDLQEntry(id: $id)
}
"""

_REPLAY_ALL_MUTATION = """
mutation ReplayAllDLQ {
  replayAllDLQ { deliveries }
}
"""

_PURGE_MUTATION = """
mutation PurgeDLQ($olderThan: String) {
  purgeDLQ(olderThan: $olderThan) { purged }
}
"""


def _parse_dlq_entry(data: dict[str, Any]) -> DLQEntry:
    return DLQEntry(
        id=data.get("id", ""),
        delivery_id=data.get("deliveryId", ""),
        event_id=data.get("eventId", ""),
        last_error=data.get("lastError", ""),
        replayed_at=data.get("replayedAt"),
        created_at=data.get("createdAt", ""),
    )


class DLQService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, event_id: str | None = None, replayed: bool | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[DLQEntry]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            eventId=event_id, replayed=replayed, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["dlqEntries"]
        return ListResult(
            nodes=[_parse_dlq_entry(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def replay(self, id: str) -> bool:
        data = self._t.execute(_REPLAY_MUTATION, {"id": id})
        return data.get("replayDLQEntry", False)

    def replay_all(self) -> ReplayResult:
        data = self._t.execute(_REPLAY_ALL_MUTATION)
        return ReplayResult(deliveries=data["replayAllDLQ"]["deliveries"])

    def purge(self, older_than: str | None = None) -> PurgeResult:
        data = self._t.execute(_PURGE_MUTATION, {"olderThan": older_than} if older_than else None)
        return PurgeResult(purged=data["purgeDLQ"]["purged"])


class AsyncDLQService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, event_id: str | None = None, replayed: bool | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[DLQEntry]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            eventId=event_id, replayed=replayed, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["dlqEntries"]
        return ListResult(
            nodes=[_parse_dlq_entry(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def replay(self, id: str) -> bool:
        data = await self._t.execute(_REPLAY_MUTATION, {"id": id})
        return data.get("replayDLQEntry", False)

    async def replay_all(self) -> ReplayResult:
        data = await self._t.execute(_REPLAY_ALL_MUTATION)
        return ReplayResult(deliveries=data["replayAllDLQ"]["deliveries"])

    async def purge(self, older_than: str | None = None) -> PurgeResult:
        data = await self._t.execute(_PURGE_MUTATION, {"olderThan": older_than} if older_than else None)
        return PurgeResult(purged=data["purgeDLQ"]["purged"])
