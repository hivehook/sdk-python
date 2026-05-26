from __future__ import annotations

from typing import Any

from hivehook.types import SystemStatus

_STATUS_QUERY = """
query GetStatus {
  status {
    status dlqSize outboundDlqSize queueDepth
    activeWorkers totalWorkers uptime version
    sourcesTotal destinationsTotal subscriptionsTotal
    eventsTotal eventsFailed
    deliveriesTotal deliveriesPending deliveriesDelivered
    messagesTotal
    outboundDeliveriesTotal outboundDeliveriesPending outboundDeliveriesFailed
  }
}
"""


def _parse_status(data: dict[str, Any]) -> SystemStatus:
    return SystemStatus(
        status=data.get("status", ""),
        dlq_size=data.get("dlqSize", 0),
        outbound_dlq_size=data.get("outboundDlqSize", 0),
        queue_depth=data.get("queueDepth", 0),
        active_workers=data.get("activeWorkers", 0),
        total_workers=data.get("totalWorkers", 0),
        uptime=data.get("uptime", 0),
        version=data.get("version", ""),
        sources_total=data.get("sourcesTotal", 0),
        destinations_total=data.get("destinationsTotal", 0),
        subscriptions_total=data.get("subscriptionsTotal", 0),
        events_total=data.get("eventsTotal", 0),
        events_failed=data.get("eventsFailed", 0),
        deliveries_total=data.get("deliveriesTotal", 0),
        deliveries_pending=data.get("deliveriesPending", 0),
        deliveries_delivered=data.get("deliveriesDelivered", 0),
        messages_total=data.get("messagesTotal", 0),
        outbound_deliveries_total=data.get("outboundDeliveriesTotal", 0),
        outbound_deliveries_pending=data.get("outboundDeliveriesPending", 0),
        outbound_deliveries_failed=data.get("outboundDeliveriesFailed", 0),
    )


class StatusService:
    def __init__(self, transport: Any):
        self._t = transport

    def get(self) -> SystemStatus:
        data = self._t.execute(_STATUS_QUERY)
        return _parse_status(data["status"])


class AsyncStatusService:
    def __init__(self, transport: Any):
        self._t = transport

    async def get(self) -> SystemStatus:
        data = await self._t.execute(_STATUS_QUERY)
        return _parse_status(data["status"])
