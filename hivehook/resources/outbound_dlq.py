from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import OutboundDLQEntry, ListResult, ReplayResult, PurgeResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_DLQ_FIELDS = "id deliveryId messageId lastError replayedAt createdAt"

_LIST_QUERY = """
query ListOutboundDLQEntries($messageId: UUID, $replayed: Boolean, $search: String,
                              $limit: Int, $offset: Int, $after: String, $first: Int) {
  outboundDlqEntries(messageId: $messageId, replayed: $replayed, search: $search,
                     limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _DLQ_FIELDS

_REPLAY_MUTATION = """
mutation ReplayOutboundDLQEntry($id: UUID!) {
  replayOutboundDlqEntry(id: $id)
}
"""

_REPLAY_ALL_MUTATION = """
mutation ReplayAllOutboundDLQ {
  replayAllOutboundDlq { deliveries }
}
"""

_PURGE_MUTATION = """
mutation PurgeOutboundDLQ($olderThan: String) {
  purgeOutboundDlq(olderThan: $olderThan) { purged }
}
"""


def _parse_outbound_dlq_entry(data: dict[str, Any]) -> OutboundDLQEntry:
    return OutboundDLQEntry(
        id=data.get("id", ""),
        delivery_id=data.get("deliveryId", ""),
        message_id=data.get("messageId", ""),
        last_error=data.get("lastError", ""),
        replayed_at=data.get("replayedAt"),
        created_at=data.get("createdAt", ""),
    )


class OutboundDLQService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, message_id: str | None = None, replayed: bool | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[OutboundDLQEntry]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            messageId=message_id, replayed=replayed, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["outboundDlqEntries"]
        return ListResult(
            nodes=[_parse_outbound_dlq_entry(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def replay(self, id: str) -> bool:
        data = self._t.execute(_REPLAY_MUTATION, {"id": id})
        return data.get("replayOutboundDlqEntry", False)

    def replay_all(self) -> ReplayResult:
        data = self._t.execute(_REPLAY_ALL_MUTATION)
        return ReplayResult(deliveries=data["replayAllOutboundDlq"]["deliveries"])

    def purge(self, older_than: str | None = None) -> PurgeResult:
        data = self._t.execute(_PURGE_MUTATION, {"olderThan": older_than} if older_than else None)
        return PurgeResult(purged=data["purgeOutboundDlq"]["purged"])

    def iterate(self, **filters: Any) -> Iterator[OutboundDLQEntry]:
        return paginate(self.list, **filters)


class AsyncOutboundDLQService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, message_id: str | None = None, replayed: bool | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[OutboundDLQEntry]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            messageId=message_id, replayed=replayed, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["outboundDlqEntries"]
        return ListResult(
            nodes=[_parse_outbound_dlq_entry(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def replay(self, id: str) -> bool:
        data = await self._t.execute(_REPLAY_MUTATION, {"id": id})
        return data.get("replayOutboundDlqEntry", False)

    async def replay_all(self) -> ReplayResult:
        data = await self._t.execute(_REPLAY_ALL_MUTATION)
        return ReplayResult(deliveries=data["replayAllOutboundDlq"]["deliveries"])

    async def purge(self, older_than: str | None = None) -> PurgeResult:
        data = await self._t.execute(_PURGE_MUTATION, {"olderThan": older_than} if older_than else None)
        return PurgeResult(purged=data["purgeOutboundDlq"]["purged"])

    def iterate(self, **filters: Any) -> AsyncIterator[OutboundDLQEntry]:
        return paginate_async(self.list, **filters)
