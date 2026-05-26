from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class RetryPolicy:
    max_attempts: int = 0
    initial_delay: str = ""
    max_delay: str = ""
    backoff_factor: float = 0.0


@dataclass
class BodyMatchRule:
    path: str = ""
    value: str = ""
    operator: str = ""


@dataclass
class FilterRule:
    operator: str = ""
    path: str | None = None
    value: Any = None
    rules: list[FilterRule] | None = None


@dataclass
class FilterConfig:
    event_types: list[str] | None = None
    regex: list[str] | None = None
    body_match: list[BodyMatchRule] | None = None
    rules: list[FilterRule] | None = None


@dataclass
class TransformConfig:
    envelope: bool = False
    headers: dict[str, Any] | None = None


@dataclass
class PageInfo:
    total: int = 0
    limit: int = 0
    offset: int = 0
    end_cursor: str | None = None
    has_next_page: bool = False


@dataclass
class ListResult(Generic[T]):
    nodes: list[T] = field(default_factory=list)
    page_info: PageInfo = field(default_factory=PageInfo)


@dataclass
class ResponseConfig:
    status_code: int = 0
    body: str = ""
    content_type: str = ""


@dataclass
class DedupConfig:
    strategy: str = ""
    fields: list[str] | None = None
    window: str | None = None


@dataclass
class Source:
    id: str = ""
    name: str = ""
    slug: str = ""
    provider_type: str = ""
    verify_config: dict[str, Any] | None = None
    status: str = ""
    rate_limit_rps: int = 0
    spike_protection: bool = False
    max_ingest_rps: int = 0
    broker_config: dict[str, Any] | None = None
    response_config: ResponseConfig | None = None
    dedup_config: DedupConfig | None = None
    created_at: str = ""


@dataclass
class OAuth2Config:
    token_url: str = ""
    client_id: str = ""
    client_secret: str = ""
    scopes: list[str] = field(default_factory=list)
    audience: str = ""


@dataclass
class HealthConfig:
    window_hours: int = 0
    disable_below: float = 0.0


@dataclass
class Destination:
    id: str = ""
    name: str = ""
    url: str = ""
    signing_secret: str = ""
    status: str = ""
    type: str = "HTTP"
    type_config: dict[str, Any] | None = None
    timeout_ms: int = 0
    rate_limit_rps: int = 0
    retry_policy: RetryPolicy | None = None
    headers: dict[str, Any] | None = None
    auth_type: str = ""
    oauth2_config: OAuth2Config | None = None
    mtls_cert: str = ""
    mtls_key: str = ""
    delivery_mode: str = ""
    poll_api_key_prefix: str = ""
    poll_api_key: str = ""
    ordered: bool = False
    blocked_delivery_id: str | None = None
    health_score: float = 1.0
    disabled_reason: str | None = None
    health_config: HealthConfig | None = None
    output_format: str = "default"
    created_at: str = ""


@dataclass
class CreateDestinationInput:
    name: str = ""
    url: str = ""
    type: str | None = None
    type_config: dict[str, Any] | None = None
    timeout_ms: int | None = None
    rate_limit_rps: int | None = None
    headers: dict[str, Any] | None = None
    retry_policy: RetryPolicy | None = None
    auth_type: str | None = None
    oauth2_config: OAuth2Config | None = None
    mtls_cert: str | None = None
    mtls_key: str | None = None
    delivery_mode: str | None = None
    ordered: bool | None = None
    health_config: HealthConfig | None = None
    output_format: str | None = None


@dataclass
class UpdateDestinationInput:
    name: str | None = None
    url: str | None = None
    status: str | None = None
    type: str | None = None
    type_config: dict[str, Any] | None = None
    timeout_ms: int | None = None
    rate_limit_rps: int | None = None
    headers: dict[str, Any] | None = None
    retry_policy: RetryPolicy | None = None
    auth_type: str | None = None
    oauth2_config: OAuth2Config | None = None
    mtls_cert: str | None = None
    mtls_key: str | None = None
    delivery_mode: str | None = None
    ordered: bool | None = None
    health_config: HealthConfig | None = None
    output_format: str | None = None


@dataclass
class Subscription:
    id: str = ""
    name: str = ""
    source_id: str = ""
    destination_id: str = ""
    filter_config: FilterConfig | None = None
    transform_config: TransformConfig | None = None
    enabled: bool = True
    created_at: str = ""


@dataclass
class Event:
    id: str = ""
    source_id: str = ""
    idempotency_key: str = ""
    event_type: str = ""
    headers: dict[str, Any] | None = None
    raw_body: str | None = None
    status: str = ""
    received_at: str = ""


@dataclass
class DeliveryAttempt:
    id: str = ""
    delivery_id: str = ""
    attempt_number: int = 0
    response_status: int = 0
    response_body: str = ""
    error: str = ""
    duration_ms: int = 0
    attempted_at: str = ""


@dataclass
class Delivery:
    id: str = ""
    event_id: str = ""
    subscription_id: str = ""
    destination_id: str = ""
    status: str = ""
    attempts: int = 0
    max_attempts: int = 0
    next_attempt_at: str | None = None
    created_at: str = ""
    delivery_attempts: list[DeliveryAttempt] | None = None


@dataclass
class DLQEntry:
    id: str = ""
    delivery_id: str = ""
    event_id: str = ""
    last_error: str = ""
    replayed_at: str | None = None
    created_at: str = ""


@dataclass
class APIKey:
    id: str = ""
    name: str = ""
    key_prefix: str = ""
    scopes: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    created_at: str = ""
    expires_at: str | None = None
    revoked_at: str | None = None
    last_used_at: str | None = None


@dataclass
class APIKeyWithSecret:
    api_key: APIKey = field(default_factory=APIKey)
    raw_key: str = ""


@dataclass
class EmailAlertConfig:
    to: list[str] = field(default_factory=list)
    subject_template: str | None = None


@dataclass
class SlackAlertConfig:
    webhook_url: str = ""
    channel: str | None = None


@dataclass
class AlertRule:
    id: str = ""
    name: str = ""
    condition_type: str = ""
    threshold: int = 0
    webhook_url: str = ""
    channel: str = "WEBHOOK"
    email_config: EmailAlertConfig | None = None
    slack_config: SlackAlertConfig | None = None
    cooldown: str = ""
    enabled: bool = True
    created_at: str = ""


@dataclass
class Bookmark:
    id: str = ""
    event_id: str = ""
    name: str = ""
    notes: str = ""
    created_at: str = ""


@dataclass
class EventTypeSchema:
    id: str = ""
    event_type: str = ""
    description: str = ""
    schema: dict[str, Any] | None = None
    example: dict[str, Any] | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Application:
    id: str = ""
    name: str = ""
    uid: str = ""
    created_at: str = ""


@dataclass
class Endpoint:
    id: str = ""
    application_id: str = ""
    url: str = ""
    signing_secret: str = ""
    filter_config: FilterConfig | None = None
    status: str = ""
    type: str = "HTTP"
    type_config: dict[str, Any] | None = None
    rate_limit_rps: int = 0
    timeout_ms: int = 0
    retry_policy: RetryPolicy | None = None
    headers: dict[str, Any] | None = None
    auth_type: str = ""
    oauth2_config: OAuth2Config | None = None
    mtls_cert: str = ""
    mtls_key: str = ""
    delivery_mode: str = ""
    poll_api_key_prefix: str = ""
    poll_api_key: str = ""
    ordered: bool = False
    blocked_delivery_id: str | None = None
    health_score: float = 1.0
    disabled_reason: str | None = None
    health_config: HealthConfig | None = None
    output_format: str = "default"
    created_at: str = ""


@dataclass
class CreateEndpointInput:
    application_id: str = ""
    url: str = ""
    type: str | None = None
    type_config: dict[str, Any] | None = None
    timeout_ms: int | None = None
    rate_limit_rps: int | None = None
    headers: dict[str, Any] | None = None
    filter_config: FilterConfig | None = None
    retry_policy: RetryPolicy | None = None
    auth_type: str | None = None
    oauth2_config: OAuth2Config | None = None
    mtls_cert: str | None = None
    mtls_key: str | None = None
    delivery_mode: str | None = None
    ordered: bool | None = None
    health_config: HealthConfig | None = None
    output_format: str | None = None


@dataclass
class UpdateEndpointInput:
    url: str | None = None
    status: str | None = None
    type: str | None = None
    type_config: dict[str, Any] | None = None
    timeout_ms: int | None = None
    rate_limit_rps: int | None = None
    headers: dict[str, Any] | None = None
    filter_config: FilterConfig | None = None
    retry_policy: RetryPolicy | None = None
    auth_type: str | None = None
    oauth2_config: OAuth2Config | None = None
    mtls_cert: str | None = None
    mtls_key: str | None = None
    delivery_mode: str | None = None
    ordered: bool | None = None
    health_config: HealthConfig | None = None
    output_format: str | None = None


@dataclass
class Message:
    id: str = ""
    application_id: str = ""
    event_type: str = ""
    payload: str | None = None
    idempotency_key: str = ""
    status: str = ""
    created_at: str = ""


@dataclass
class OutboundDeliveryAttempt:
    id: str = ""
    delivery_id: str = ""
    attempt_number: int = 0
    response_status: int = 0
    response_body: str = ""
    error: str = ""
    duration_ms: int = 0
    attempted_at: str = ""


@dataclass
class OutboundDelivery:
    id: str = ""
    message_id: str = ""
    endpoint_id: str = ""
    status: str = ""
    attempts: int = 0
    max_attempts: int = 0
    next_attempt_at: str | None = None
    created_at: str = ""
    delivery_attempts: list[OutboundDeliveryAttempt] | None = None


@dataclass
class OutboundDLQEntry:
    id: str = ""
    delivery_id: str = ""
    message_id: str = ""
    last_error: str = ""
    replayed_at: str | None = None
    created_at: str = ""


@dataclass
class SystemStatus:
    status: str = ""
    dlq_size: int = 0
    outbound_dlq_size: int = 0
    queue_depth: int = 0
    active_workers: int = 0
    total_workers: int = 0
    uptime: int = 0
    version: str = ""
    sources_total: int = 0
    destinations_total: int = 0
    subscriptions_total: int = 0
    events_total: int = 0
    events_failed: int = 0
    deliveries_total: int = 0
    deliveries_pending: int = 0
    deliveries_delivered: int = 0
    messages_total: int = 0
    outbound_deliveries_total: int = 0
    outbound_deliveries_pending: int = 0
    outbound_deliveries_failed: int = 0


@dataclass
class ReplayResult:
    deliveries: int = 0


@dataclass
class PurgeResult:
    purged: int = 0


@dataclass
class Transformation:
    id: str = ""
    name: str = ""
    description: str = ""
    code: str = ""
    enabled: bool = True
    fail_open: bool = False
    timeout_ms: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class ListTransformationsOptions:
    enabled: bool | None = None
    search: str | None = None
    after: str | None = None
    first: int | None = None


@dataclass
class CreateTransformationInput:
    name: str = ""
    description: str = ""
    code: str = ""
    fail_open: bool = False
    timeout_ms: int = 0


@dataclass
class UpdateTransformationInput:
    name: str | None = None
    description: str | None = None
    code: str | None = None
    enabled: bool | None = None
    fail_open: bool | None = None
    timeout_ms: int | None = None


@dataclass
class TestTransformationInput:
    code: str = ""
    payload: dict[str, Any] | None = None
    event_type: str | None = None
    headers: dict[str, Any] | None = None


@dataclass
class TransformTestResult:
    success: bool = False
    output: dict[str, Any] | None = None
    error: str = ""
    duration_ms: int = 0


@dataclass
class OTLPConfig:
    endpoint: str = ""
    headers: dict[str, str] | None = None
    insecure: bool = False
    sample_rate: float = 0.0


@dataclass
class Organization:
    id: str = ""
    name: str = ""
    slug: str = ""
    sso_enabled: bool = False
    sso_provider: str | None = None
    retention_events: int = 0
    retention_messages: int = 0
    otlp_config: OTLPConfig | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class User:
    id: str = ""
    organization_id: str = ""
    email: str = ""
    name: str = ""
    role: str = ""
    last_login_at: str | None = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class AuditLog:
    id: str = ""
    actor_type: str = ""
    actor_id: str = ""
    actor_name: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    org_id: str = ""
    ip_address: str = ""
    user_agent: str = ""
    details: Any | None = None
    created_at: str = ""


@dataclass
class Stream:
    id: str = ""
    application_id: str = ""
    name: str = ""
    status: str = ""
    retention_days: int = 0
    created_at: str = ""


@dataclass
class StreamConsumer:
    id: str = ""
    stream_id: str = ""
    name: str = ""
    cursor_sequence: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class StreamSink:
    id: str = ""
    stream_id: str = ""
    name: str = ""
    sink_type: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    batch_size: int = 0
    flush_interval: str = ""
    cursor_sequence: int = 0
    status: str = ""
    last_flushed_at: str | None = None
    created_at: str = ""
