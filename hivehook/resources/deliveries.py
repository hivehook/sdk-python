from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import Delivery, DeliveryAttempt, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_DELIVERY_FIELDS = """
    id eventId subscriptionId destinationId
    status attempts maxAttempts nextAttemptAt createdAt
    deliveryAttempts {
      id deliveryId attemptNumber responseStatus
      responseBody error durationMs attemptedAt
    }
"""

_LIST_QUERY = """
query ListDeliveries($eventId: UUID, $destinationId: UUID, $subscriptionId: UUID,
                      $status: DeliveryStatus, $search: String,
                      $limit: Int, $offset: Int, $after: String, $first: Int) {
  deliveries(eventId: $eventId, destinationId: $destinationId, subscriptionId: $subscriptionId,
             status: $status, search: $search,
             limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _DELIVERY_FIELDS

_GET_QUERY = """
query GetDelivery($id: UUID!) {
  delivery(id: $id) { %s }
}
""" % _DELIVERY_FIELDS


def _parse_attempt(data: dict[str, Any]) -> DeliveryAttempt:
    return DeliveryAttempt(
        id=data.get("id", ""),
        delivery_id=data.get("deliveryId", ""),
        attempt_number=data.get("attemptNumber", 0),
        response_status=data.get("responseStatus", 0),
        response_body=data.get("responseBody", ""),
        error=data.get("error", ""),
        duration_ms=data.get("durationMs", 0),
        attempted_at=data.get("attemptedAt", ""),
    )


def _parse_delivery(data: dict[str, Any]) -> Delivery:
    attempts = None
    if data.get("deliveryAttempts"):
        attempts = [_parse_attempt(a) for a in data["deliveryAttempts"]]
    return Delivery(
        id=data.get("id", ""),
        event_id=data.get("eventId", ""),
        subscription_id=data.get("subscriptionId", ""),
        destination_id=data.get("destinationId", ""),
        status=data.get("status", ""),
        attempts=data.get("attempts", 0),
        max_attempts=data.get("maxAttempts", 0),
        next_attempt_at=data.get("nextAttemptAt"),
        created_at=data.get("createdAt", ""),
        delivery_attempts=attempts,
    )


class DeliveryService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, event_id: str | None = None, destination_id: str | None = None,
        subscription_id: str | None = None, status: str | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Delivery]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            eventId=event_id, destinationId=destination_id,
                            subscriptionId=subscription_id, status=status, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["deliveries"]
        return ListResult(
            nodes=[_parse_delivery(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Delivery | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        d = data.get("delivery")
        return _parse_delivery(d) if d else None

    def iterate(self, **filters: Any) -> Iterator[Delivery]:
        return paginate(self.list, **filters)


class AsyncDeliveryService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, event_id: str | None = None, destination_id: str | None = None,
        subscription_id: str | None = None, status: str | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Delivery]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            eventId=event_id, destinationId=destination_id,
                            subscriptionId=subscription_id, status=status, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["deliveries"]
        return ListResult(
            nodes=[_parse_delivery(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Delivery | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        d = data.get("delivery")
        return _parse_delivery(d) if d else None

    def iterate(self, **filters: Any) -> AsyncIterator[Delivery]:
        return paginate_async(self.list, **filters)
