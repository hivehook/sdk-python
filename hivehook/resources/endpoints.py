from __future__ import annotations

from typing import Any

from hivehook.types import Endpoint, ListResult, RetryPolicy, OAuth2Config, OutboundDelivery, HealthConfig
from hivehook.resources._base import parse_page_info, build_list_vars
from hivehook.resources.subscriptions import _parse_filter_config, _build_filter_config_input
from hivehook.resources.destinations import _parse_oauth2_config, _build_oauth2_config_input, _parse_health_config, _build_health_config_input
from hivehook.resources.outbound_deliveries import _parse_outbound_delivery

_ENDPOINT_FIELDS = """
    id applicationId url signingSecret
    filterConfig {
      eventTypes regex
      bodyMatch { path value operator }
      rules { path operator value rules { path operator value } }
    }
    status type typeConfig rateLimitRps timeoutMs
    retryPolicy { maxAttempts initialDelay maxDelay backoffFactor }
    headers
    authType
    oauth2Config { tokenUrl clientId clientSecret scopes audience }
    mtlsCert mtlsKey
    deliveryMode pollApiKeyPrefix pollApiKey
    ordered blockedDeliveryId
    healthScore disabledReason
    healthConfig { windowHours disableBelow }
    outputFormat
    createdAt
"""

_LIST_QUERY = """
query ListEndpoints($applicationId: UUID, $status: EndpointStatus, $search: String,
                     $limit: Int, $offset: Int, $after: String, $first: Int) {
  endpoints(applicationId: $applicationId, status: $status, search: $search,
            limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _ENDPOINT_FIELDS

_GET_QUERY = """
query GetEndpoint($id: UUID!) {
  endpoint(id: $id) { %s }
}
""" % _ENDPOINT_FIELDS

_CREATE_MUTATION = """
mutation CreateEndpoint($input: CreateEndpointInput!) {
  createEndpoint(input: $input) { %s }
}
""" % _ENDPOINT_FIELDS

_UPDATE_MUTATION = """
mutation UpdateEndpoint($id: UUID!, $input: UpdateEndpointInput!) {
  updateEndpoint(id: $id, input: $input) { %s }
}
""" % _ENDPOINT_FIELDS

_DELETE_MUTATION = """
mutation DeleteEndpoint($id: UUID!) {
  deleteEndpoint(id: $id)
}
"""

_ROTATE_SECRET_MUTATION = """
mutation RotateEndpointSecret($id: UUID!) {
  rotateEndpointSecret(id: $id) { %s }
}
""" % _ENDPOINT_FIELDS

_POLL_OUTBOUND_DELIVERIES_QUERY = """
query PollOutboundDeliveries($endpointId: UUID!, $cursor: String, $limit: Int) {
  pollOutboundDeliveries(endpointId: $endpointId, cursor: $cursor, limit: $limit) {
    nodes { id messageId endpointId status attempts maxAttempts nextAttemptAt createdAt }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
"""

_ACK_OUTBOUND_DELIVERIES_MUTATION = """
mutation AckOutboundDeliveries($endpointId: UUID!, $deliveryIds: [UUID!]!) {
  ackOutboundDeliveries(endpointId: $endpointId, deliveryIds: $deliveryIds)
}
"""

_REGENERATE_OUTBOUND_POLL_API_KEY_MUTATION = """
mutation RegenerateOutboundPollApiKey($endpointId: UUID!) {
  regenerateOutboundPollApiKey(endpointId: $endpointId) { %s }
}
""" % _ENDPOINT_FIELDS

_SKIP_OUTBOUND_DLQ_ENTRY_MUTATION = """
mutation SkipOutboundDLQEntry($id: UUID!) {
  skipOutboundDlqEntry(id: $id)
}
"""


def _parse_retry_policy(data: dict[str, Any] | None) -> RetryPolicy | None:
    if not data:
        return None
    return RetryPolicy(
        max_attempts=data.get("maxAttempts", 0),
        initial_delay=data.get("initialDelay", ""),
        max_delay=data.get("maxDelay", ""),
        backoff_factor=data.get("backoffFactor", 0.0),
    )


def _parse_endpoint(data: dict[str, Any]) -> Endpoint:
    return Endpoint(
        id=data.get("id", ""),
        application_id=data.get("applicationId", ""),
        url=data.get("url", ""),
        signing_secret=data.get("signingSecret", ""),
        filter_config=_parse_filter_config(data.get("filterConfig")),
        status=data.get("status", ""),
        type=data.get("type", "HTTP"),
        type_config=data.get("typeConfig"),
        rate_limit_rps=data.get("rateLimitRps", 0),
        timeout_ms=data.get("timeoutMs", 0),
        retry_policy=_parse_retry_policy(data.get("retryPolicy")),
        headers=data.get("headers"),
        auth_type=data.get("authType", ""),
        oauth2_config=_parse_oauth2_config(data.get("oauth2Config")),
        mtls_cert=data.get("mtlsCert", ""),
        mtls_key=data.get("mtlsKey", ""),
        delivery_mode=data.get("deliveryMode", ""),
        poll_api_key_prefix=data.get("pollApiKeyPrefix", ""),
        poll_api_key=data.get("pollApiKey", ""),
        ordered=data.get("ordered", False),
        blocked_delivery_id=data.get("blockedDeliveryId"),
        health_score=data.get("healthScore", 1.0),
        disabled_reason=data.get("disabledReason"),
        health_config=_parse_health_config(data.get("healthConfig")),
        output_format=data.get("outputFormat", "default"),
        created_at=data.get("createdAt", ""),
    )


class EndpointService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, application_id: str | None = None, status: str | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Endpoint]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            applicationId=application_id, status=status, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["endpoints"]
        return ListResult(
            nodes=[_parse_endpoint(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Endpoint | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        e = data.get("endpoint")
        return _parse_endpoint(e) if e else None

    def create(self, application_id: str, url: str, **kwargs: Any) -> Endpoint:
        inp: dict[str, Any] = {"applicationId": application_id, "url": url}
        key_map = {"type": "type", "type_config": "typeConfig",
                    "timeout_ms": "timeoutMs", "rate_limit_rps": "rateLimitRps",
                    "headers": "headers", "auth_type": "authType",
                    "mtls_cert": "mtlsCert", "mtls_key": "mtlsKey",
                    "delivery_mode": "deliveryMode", "ordered": "ordered",
                    "output_format": "outputFormat"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "filter_config" in kwargs and kwargs["filter_config"] is not None:
            inp["filterConfig"] = _build_filter_config_input(kwargs["filter_config"])
        if "retry_policy" in kwargs and kwargs["retry_policy"] is not None:
            rp = kwargs["retry_policy"]
            inp["retryPolicy"] = {"maxAttempts": rp.max_attempts, "initialDelay": rp.initial_delay,
                                  "maxDelay": rp.max_delay, "backoffFactor": rp.backoff_factor}
        if "oauth2_config" in kwargs and kwargs["oauth2_config"] is not None:
            oc = kwargs["oauth2_config"]
            if isinstance(oc, OAuth2Config):
                oc = _build_oauth2_config_input(oc)
            inp["oauth2Config"] = oc
        if "health_config" in kwargs and kwargs["health_config"] is not None:
            hc = kwargs["health_config"]
            if isinstance(hc, HealthConfig):
                hc = _build_health_config_input(hc)
            inp["healthConfig"] = hc
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_endpoint(data["createEndpoint"])

    def update(self, id: str, **kwargs: Any) -> Endpoint:
        inp: dict[str, Any] = {}
        key_map = {"url": "url", "status": "status", "type": "type",
                    "type_config": "typeConfig", "timeout_ms": "timeoutMs",
                    "rate_limit_rps": "rateLimitRps", "headers": "headers",
                    "auth_type": "authType", "mtls_cert": "mtlsCert", "mtls_key": "mtlsKey",
                    "delivery_mode": "deliveryMode", "ordered": "ordered",
                    "output_format": "outputFormat"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "filter_config" in kwargs and kwargs["filter_config"] is not None:
            inp["filterConfig"] = _build_filter_config_input(kwargs["filter_config"])
        if "retry_policy" in kwargs and kwargs["retry_policy"] is not None:
            rp = kwargs["retry_policy"]
            inp["retryPolicy"] = {"maxAttempts": rp.max_attempts, "initialDelay": rp.initial_delay,
                                  "maxDelay": rp.max_delay, "backoffFactor": rp.backoff_factor}
        if "oauth2_config" in kwargs and kwargs["oauth2_config"] is not None:
            oc = kwargs["oauth2_config"]
            if isinstance(oc, OAuth2Config):
                oc = _build_oauth2_config_input(oc)
            inp["oauth2Config"] = oc
        if "health_config" in kwargs and kwargs["health_config"] is not None:
            hc = kwargs["health_config"]
            if isinstance(hc, HealthConfig):
                hc = _build_health_config_input(hc)
            inp["healthConfig"] = hc
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_endpoint(data["updateEndpoint"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteEndpoint", False)

    def rotate_secret(self, id: str) -> Endpoint:
        data = self._t.execute(_ROTATE_SECRET_MUTATION, {"id": id})
        return _parse_endpoint(data["rotateEndpointSecret"])

    def poll_deliveries(
        self, endpoint_id: str, cursor: str | None = None, limit: int | None = None,
    ) -> ListResult[OutboundDelivery]:
        v: dict[str, Any] = {"endpointId": endpoint_id}
        if cursor is not None:
            v["cursor"] = cursor
        if limit is not None:
            v["limit"] = limit
        data = self._t.execute(_POLL_OUTBOUND_DELIVERIES_QUERY, v)
        conn = data["pollOutboundDeliveries"]
        return ListResult(
            nodes=[_parse_outbound_delivery(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def ack_deliveries(self, endpoint_id: str, delivery_ids: list[str]) -> int:
        data = self._t.execute(_ACK_OUTBOUND_DELIVERIES_MUTATION, {"endpointId": endpoint_id, "deliveryIds": delivery_ids})
        return data.get("ackOutboundDeliveries", 0)

    def regenerate_poll_api_key(self, endpoint_id: str) -> Endpoint:
        data = self._t.execute(_REGENERATE_OUTBOUND_POLL_API_KEY_MUTATION, {"endpointId": endpoint_id})
        return _parse_endpoint(data["regenerateOutboundPollApiKey"])

    def skip_outbound_dlq_entry(self, id: str) -> bool:
        data = self._t.execute(_SKIP_OUTBOUND_DLQ_ENTRY_MUTATION, {"id": id})
        return data.get("skipOutboundDlqEntry", False)


class AsyncEndpointService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, application_id: str | None = None, status: str | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Endpoint]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            applicationId=application_id, status=status, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["endpoints"]
        return ListResult(
            nodes=[_parse_endpoint(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Endpoint | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        e = data.get("endpoint")
        return _parse_endpoint(e) if e else None

    async def create(self, application_id: str, url: str, **kwargs: Any) -> Endpoint:
        inp: dict[str, Any] = {"applicationId": application_id, "url": url}
        key_map = {"type": "type", "type_config": "typeConfig",
                    "timeout_ms": "timeoutMs", "rate_limit_rps": "rateLimitRps",
                    "headers": "headers", "auth_type": "authType",
                    "mtls_cert": "mtlsCert", "mtls_key": "mtlsKey",
                    "delivery_mode": "deliveryMode", "ordered": "ordered",
                    "output_format": "outputFormat"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "filter_config" in kwargs and kwargs["filter_config"] is not None:
            inp["filterConfig"] = _build_filter_config_input(kwargs["filter_config"])
        if "retry_policy" in kwargs and kwargs["retry_policy"] is not None:
            rp = kwargs["retry_policy"]
            inp["retryPolicy"] = {"maxAttempts": rp.max_attempts, "initialDelay": rp.initial_delay,
                                  "maxDelay": rp.max_delay, "backoffFactor": rp.backoff_factor}
        if "oauth2_config" in kwargs and kwargs["oauth2_config"] is not None:
            oc = kwargs["oauth2_config"]
            if isinstance(oc, OAuth2Config):
                oc = _build_oauth2_config_input(oc)
            inp["oauth2Config"] = oc
        if "health_config" in kwargs and kwargs["health_config"] is not None:
            hc = kwargs["health_config"]
            if isinstance(hc, HealthConfig):
                hc = _build_health_config_input(hc)
            inp["healthConfig"] = hc
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_endpoint(data["createEndpoint"])

    async def update(self, id: str, **kwargs: Any) -> Endpoint:
        inp: dict[str, Any] = {}
        key_map = {"url": "url", "status": "status", "type": "type",
                    "type_config": "typeConfig", "timeout_ms": "timeoutMs",
                    "rate_limit_rps": "rateLimitRps", "headers": "headers",
                    "auth_type": "authType", "mtls_cert": "mtlsCert", "mtls_key": "mtlsKey",
                    "delivery_mode": "deliveryMode", "ordered": "ordered",
                    "output_format": "outputFormat"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "filter_config" in kwargs and kwargs["filter_config"] is not None:
            inp["filterConfig"] = _build_filter_config_input(kwargs["filter_config"])
        if "retry_policy" in kwargs and kwargs["retry_policy"] is not None:
            rp = kwargs["retry_policy"]
            inp["retryPolicy"] = {"maxAttempts": rp.max_attempts, "initialDelay": rp.initial_delay,
                                  "maxDelay": rp.max_delay, "backoffFactor": rp.backoff_factor}
        if "oauth2_config" in kwargs and kwargs["oauth2_config"] is not None:
            oc = kwargs["oauth2_config"]
            if isinstance(oc, OAuth2Config):
                oc = _build_oauth2_config_input(oc)
            inp["oauth2Config"] = oc
        if "health_config" in kwargs and kwargs["health_config"] is not None:
            hc = kwargs["health_config"]
            if isinstance(hc, HealthConfig):
                hc = _build_health_config_input(hc)
            inp["healthConfig"] = hc
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_endpoint(data["updateEndpoint"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteEndpoint", False)

    async def rotate_secret(self, id: str) -> Endpoint:
        data = await self._t.execute(_ROTATE_SECRET_MUTATION, {"id": id})
        return _parse_endpoint(data["rotateEndpointSecret"])

    async def poll_deliveries(
        self, endpoint_id: str, cursor: str | None = None, limit: int | None = None,
    ) -> ListResult[OutboundDelivery]:
        v: dict[str, Any] = {"endpointId": endpoint_id}
        if cursor is not None:
            v["cursor"] = cursor
        if limit is not None:
            v["limit"] = limit
        data = await self._t.execute(_POLL_OUTBOUND_DELIVERIES_QUERY, v)
        conn = data["pollOutboundDeliveries"]
        return ListResult(
            nodes=[_parse_outbound_delivery(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def ack_deliveries(self, endpoint_id: str, delivery_ids: list[str]) -> int:
        data = await self._t.execute(_ACK_OUTBOUND_DELIVERIES_MUTATION, {"endpointId": endpoint_id, "deliveryIds": delivery_ids})
        return data.get("ackOutboundDeliveries", 0)

    async def regenerate_poll_api_key(self, endpoint_id: str) -> Endpoint:
        data = await self._t.execute(_REGENERATE_OUTBOUND_POLL_API_KEY_MUTATION, {"endpointId": endpoint_id})
        return _parse_endpoint(data["regenerateOutboundPollApiKey"])

    async def skip_outbound_dlq_entry(self, id: str) -> bool:
        data = await self._t.execute(_SKIP_OUTBOUND_DLQ_ENTRY_MUTATION, {"id": id})
        return data.get("skipOutboundDlqEntry", False)
