from __future__ import annotations

from typing import Any

from hivehook._async_transport import AsyncTransport
from hivehook.resources import (
    AsyncSourceService, AsyncDestinationService, AsyncSubscriptionService,
    AsyncEventService, AsyncDeliveryService, AsyncDLQService,
    AsyncAPIKeyService, AsyncAlertRuleService, AsyncBookmarkService,
    AsyncEventTypeSchemaService, AsyncApplicationService, AsyncEndpointService,
    AsyncMessageService, AsyncOutboundDeliveryService, AsyncOutboundDLQService,
    AsyncStatusService, AsyncTransformationService, AsyncPortalService,
    AsyncStreamService, AsyncStreamConsumerService, AsyncStreamSinkService,
    AsyncOrganizationService, AsyncUserService, AsyncAuditLogService,
)


class AsyncHivehookClient:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "http://localhost:8080",
        client: Any | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        t = AsyncTransport(
            base_url,
            api_key,
            client,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._transport = t
        self.sources = AsyncSourceService(t)
        self.destinations = AsyncDestinationService(t)
        self.subscriptions = AsyncSubscriptionService(t)
        self.events = AsyncEventService(t)
        self.deliveries = AsyncDeliveryService(t)
        self.dlq = AsyncDLQService(t)
        self.api_keys = AsyncAPIKeyService(t)
        self.alert_rules = AsyncAlertRuleService(t)
        self.bookmarks = AsyncBookmarkService(t)
        self.event_type_schemas = AsyncEventTypeSchemaService(t)
        self.applications = AsyncApplicationService(t)
        self.endpoints = AsyncEndpointService(t)
        self.messages = AsyncMessageService(t)
        self.outbound_deliveries = AsyncOutboundDeliveryService(t)
        self.outbound_dlq = AsyncOutboundDLQService(t)
        self.status = AsyncStatusService(t)
        self.transformations = AsyncTransformationService(t)
        self.portal = AsyncPortalService(t)
        self.streams = AsyncStreamService(t)
        self.stream_consumers = AsyncStreamConsumerService(t)
        self.stream_sinks = AsyncStreamSinkService(t)
        self.organizations = AsyncOrganizationService(t)
        self.users = AsyncUserService(t)
        self.audit_logs = AsyncAuditLogService(t)

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> AsyncHivehookClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
