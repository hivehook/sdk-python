from __future__ import annotations

from typing import Any

from hivehook.types import OutboundDelivery, OutboundDeliveryAttempt, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars

_DELIVERY_FIELDS = """
    id messageId endpointId
    status attempts maxAttempts nextAttemptAt createdAt
    deliveryAttempts {
      id deliveryId attemptNumber responseStatus
      responseBody error durationMs attemptedAt
    }
"""

_LIST_QUERY = """
query ListOutboundDeliveries($messageId: UUID, $endpointId: UUID, $status: DeliveryStatus,
                              $search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  outboundDeliveries(messageId: $messageId, endpointId: $endpointId, status: $status,
                     search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _DELIVERY_FIELDS

_GET_QUERY = """
query GetOutboundDelivery($id: UUID!) {
  outboundDelivery(id: $id) { %s }
}
""" % _DELIVERY_FIELDS


def _parse_attempt(data: dict[str, Any]) -> OutboundDeliveryAttempt:
    return OutboundDeliveryAttempt(
        id=data.get("id", ""),
        delivery_id=data.get("deliveryId", ""),
        attempt_number=data.get("attemptNumber", 0),
        response_status=data.get("responseStatus", 0),
        response_body=data.get("responseBody", ""),
        error=data.get("error", ""),
        duration_ms=data.get("durationMs", 0),
        attempted_at=data.get("attemptedAt", ""),
    )


def _parse_outbound_delivery(data: dict[str, Any]) -> OutboundDelivery:
    attempts = None
    if data.get("deliveryAttempts"):
        attempts = [_parse_attempt(a) for a in data["deliveryAttempts"]]
    return OutboundDelivery(
        id=data.get("id", ""),
        message_id=data.get("messageId", ""),
        endpoint_id=data.get("endpointId", ""),
        status=data.get("status", ""),
        attempts=data.get("attempts", 0),
        max_attempts=data.get("maxAttempts", 0),
        next_attempt_at=data.get("nextAttemptAt"),
        created_at=data.get("createdAt", ""),
        delivery_attempts=attempts,
    )


class OutboundDeliveryService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, message_id: str | None = None, endpoint_id: str | None = None,
        status: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[OutboundDelivery]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            messageId=message_id, endpointId=endpoint_id,
                            status=status, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["outboundDeliveries"]
        return ListResult(
            nodes=[_parse_outbound_delivery(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> OutboundDelivery | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        d = data.get("outboundDelivery")
        return _parse_outbound_delivery(d) if d else None


class AsyncOutboundDeliveryService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, message_id: str | None = None, endpoint_id: str | None = None,
        status: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[OutboundDelivery]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            messageId=message_id, endpointId=endpoint_id,
                            status=status, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["outboundDeliveries"]
        return ListResult(
            nodes=[_parse_outbound_delivery(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> OutboundDelivery | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        d = data.get("outboundDelivery")
        return _parse_outbound_delivery(d) if d else None
