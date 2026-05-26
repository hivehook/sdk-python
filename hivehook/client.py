from __future__ import annotations

from typing import Any

import requests

from hivehook._transport import Transport
from hivehook.resources import (
    SourceService, DestinationService, SubscriptionService,
    EventService, DeliveryService, DLQService,
    APIKeyService, AlertRuleService, BookmarkService,
    EventTypeSchemaService, ApplicationService, EndpointService,
    MessageService, OutboundDeliveryService, OutboundDLQService,
    StatusService, TransformationService, PortalService,
    StreamService, StreamConsumerService, StreamSinkService,
    OrganizationService, UserService, AuditLogService,
)


class HivehookClient:
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "http://localhost:8080",
        session: requests.Session | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
    ):
        t = Transport(
            base_url,
            api_key,
            session,
            timeout=timeout,
            max_retries=max_retries,
        )
        self._transport = t
        self.sources = SourceService(t)
        self.destinations = DestinationService(t)
        self.subscriptions = SubscriptionService(t)
        self.events = EventService(t)
        self.deliveries = DeliveryService(t)
        self.dlq = DLQService(t)
        self.api_keys = APIKeyService(t)
        self.alert_rules = AlertRuleService(t)
        self.bookmarks = BookmarkService(t)
        self.event_type_schemas = EventTypeSchemaService(t)
        self.applications = ApplicationService(t)
        self.endpoints = EndpointService(t)
        self.messages = MessageService(t)
        self.outbound_deliveries = OutboundDeliveryService(t)
        self.outbound_dlq = OutboundDLQService(t)
        self.status = StatusService(t)
        self.transformations = TransformationService(t)
        self.portal = PortalService(t)
        self.streams = StreamService(t)
        self.stream_consumers = StreamConsumerService(t)
        self.stream_sinks = StreamSinkService(t)
        self.organizations = OrganizationService(t)
        self.users = UserService(t)
        self.audit_logs = AuditLogService(t)

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> HivehookClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
