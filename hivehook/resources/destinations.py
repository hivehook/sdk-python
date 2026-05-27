from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import Destination, ListResult, RetryPolicy, OAuth2Config, Delivery, HealthConfig
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async
from hivehook.resources.deliveries import _parse_delivery

_DEST_FIELDS = """
    id name url signingSecret status type typeConfig timeoutMs rateLimitRps
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
query ListDestinations($status: DestinationStatus, $search: String,
                        $limit: Int, $offset: Int, $after: String, $first: Int) {
  destinations(status: $status, search: $search,
               limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _DEST_FIELDS

_GET_QUERY = """
query GetDestination($id: UUID!) {
  destination(id: $id) { %s }
}
""" % _DEST_FIELDS

_CREATE_MUTATION = """
mutation CreateDestination($input: CreateDestinationInput!) {
  createDestination(input: $input) { %s }
}
""" % _DEST_FIELDS

_UPDATE_MUTATION = """
mutation UpdateDestination($id: UUID!, $input: UpdateDestinationInput!) {
  updateDestination(id: $id, input: $input) { %s }
}
""" % _DEST_FIELDS

_DELETE_MUTATION = """
mutation DeleteDestination($id: UUID!) {
  deleteDestination(id: $id)
}
"""

_ROTATE_SECRET_MUTATION = """
mutation RotateDestinationSecret($id: UUID!) {
  rotateDestinationSecret(id: $id) { %s }
}
""" % _DEST_FIELDS

_POLL_DELIVERIES_QUERY = """
query PollDeliveries($destinationId: UUID!, $cursor: String, $limit: Int) {
  pollDeliveries(destinationId: $destinationId, cursor: $cursor, limit: $limit) {
    nodes { id eventId subscriptionId destinationId status attempts maxAttempts nextAttemptAt createdAt }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
"""

_ACK_DELIVERIES_MUTATION = """
mutation AckDeliveries($destinationId: UUID!, $deliveryIds: [UUID!]!) {
  ackDeliveries(destinationId: $destinationId, deliveryIds: $deliveryIds)
}
"""

_REGENERATE_POLL_API_KEY_MUTATION = """
mutation RegeneratePollApiKey($destinationId: UUID!) {
  regeneratePollApiKey(destinationId: $destinationId) { %s }
}
""" % _DEST_FIELDS

_SKIP_DLQ_ENTRY_MUTATION = """
mutation SkipDLQEntry($id: UUID!) {
  skipDLQEntry(id: $id)
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


def _parse_oauth2_config(data: dict[str, Any] | None) -> OAuth2Config | None:
    if not data:
        return None
    return OAuth2Config(
        token_url=data.get("tokenUrl", ""),
        client_id=data.get("clientId", ""),
        client_secret=data.get("clientSecret", ""),
        scopes=data.get("scopes", []),
        audience=data.get("audience", ""),
    )


def _parse_health_config(data: dict[str, Any] | None) -> HealthConfig | None:
    if not data:
        return None
    return HealthConfig(
        window_hours=data.get("windowHours", 0),
        disable_below=data.get("disableBelow", 0.0),
    )


def _build_health_config_input(cfg: HealthConfig) -> dict[str, Any]:
    return {
        "windowHours": cfg.window_hours,
        "disableBelow": cfg.disable_below,
    }


def _build_oauth2_config_input(cfg: OAuth2Config) -> dict[str, Any]:
    return {
        "tokenUrl": cfg.token_url,
        "clientId": cfg.client_id,
        "clientSecret": cfg.client_secret,
        "scopes": cfg.scopes,
        "audience": cfg.audience,
    }


def _parse_destination(data: dict[str, Any]) -> Destination:
    return Destination(
        id=data.get("id", ""),
        name=data.get("name", ""),
        url=data.get("url", ""),
        signing_secret=data.get("signingSecret", ""),
        status=data.get("status", ""),
        type=data.get("type", "HTTP"),
        type_config=data.get("typeConfig"),
        timeout_ms=data.get("timeoutMs", 0),
        rate_limit_rps=data.get("rateLimitRps", 0),
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


class DestinationService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, status: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Destination]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            status=status, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["destinations"]
        return ListResult(
            nodes=[_parse_destination(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Destination | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        d = data.get("destination")
        return _parse_destination(d) if d else None

    def create(self, name: str, url: str, **kwargs: Any) -> Destination:
        inp: dict[str, Any] = {"name": name, "url": url}
        key_map = {"type": "type", "type_config": "typeConfig",
                    "timeout_ms": "timeoutMs", "rate_limit_rps": "rateLimitRps",
                    "headers": "headers", "auth_type": "authType",
                    "mtls_cert": "mtlsCert", "mtls_key": "mtlsKey",
                    "delivery_mode": "deliveryMode", "ordered": "ordered",
                    "output_format": "outputFormat"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "retry_policy" in kwargs and kwargs["retry_policy"] is not None:
            rp = kwargs["retry_policy"]
            if isinstance(rp, RetryPolicy):
                rp = {"maxAttempts": rp.max_attempts, "initialDelay": rp.initial_delay,
                       "maxDelay": rp.max_delay, "backoffFactor": rp.backoff_factor}
            inp["retryPolicy"] = rp
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
        return _parse_destination(data["createDestination"])

    def update(self, id: str, **kwargs: Any) -> Destination:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "url": "url", "status": "status",
                    "type": "type", "type_config": "typeConfig",
                    "timeout_ms": "timeoutMs", "rate_limit_rps": "rateLimitRps",
                    "headers": "headers", "auth_type": "authType",
                    "mtls_cert": "mtlsCert", "mtls_key": "mtlsKey",
                    "delivery_mode": "deliveryMode", "ordered": "ordered",
                    "output_format": "outputFormat"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "retry_policy" in kwargs and kwargs["retry_policy"] is not None:
            rp = kwargs["retry_policy"]
            if isinstance(rp, RetryPolicy):
                rp = {"maxAttempts": rp.max_attempts, "initialDelay": rp.initial_delay,
                       "maxDelay": rp.max_delay, "backoffFactor": rp.backoff_factor}
            inp["retryPolicy"] = rp
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
        return _parse_destination(data["updateDestination"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteDestination", False)

    def rotate_secret(self, id: str) -> Destination:
        data = self._t.execute(_ROTATE_SECRET_MUTATION, {"id": id})
        return _parse_destination(data["rotateDestinationSecret"])

    def poll_deliveries(
        self, destination_id: str, cursor: str | None = None, limit: int | None = None,
    ) -> ListResult[Delivery]:
        v: dict[str, Any] = {"destinationId": destination_id}
        if cursor is not None:
            v["cursor"] = cursor
        if limit is not None:
            v["limit"] = limit
        data = self._t.execute(_POLL_DELIVERIES_QUERY, v)
        conn = data["pollDeliveries"]
        return ListResult(
            nodes=[_parse_delivery(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def ack_deliveries(self, destination_id: str, delivery_ids: list[str]) -> int:
        data = self._t.execute(_ACK_DELIVERIES_MUTATION, {"destinationId": destination_id, "deliveryIds": delivery_ids})
        return data.get("ackDeliveries", 0)

    def regenerate_poll_api_key(self, destination_id: str) -> Destination:
        data = self._t.execute(_REGENERATE_POLL_API_KEY_MUTATION, {"destinationId": destination_id})
        return _parse_destination(data["regeneratePollApiKey"])

    def skip_dlq_entry(self, id: str) -> bool:
        data = self._t.execute(_SKIP_DLQ_ENTRY_MUTATION, {"id": id})
        return data.get("skipDLQEntry", False)

    def iterate(self, **filters: Any) -> Iterator[Destination]:
        return paginate(self.list, **filters)


class AsyncDestinationService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, status: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Destination]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            status=status, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["destinations"]
        return ListResult(
            nodes=[_parse_destination(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Destination | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        d = data.get("destination")
        return _parse_destination(d) if d else None

    async def create(self, name: str, url: str, **kwargs: Any) -> Destination:
        inp: dict[str, Any] = {"name": name, "url": url}
        key_map = {"type": "type", "type_config": "typeConfig",
                    "timeout_ms": "timeoutMs", "rate_limit_rps": "rateLimitRps",
                    "headers": "headers", "auth_type": "authType",
                    "mtls_cert": "mtlsCert", "mtls_key": "mtlsKey",
                    "delivery_mode": "deliveryMode", "ordered": "ordered",
                    "output_format": "outputFormat"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "retry_policy" in kwargs and kwargs["retry_policy"] is not None:
            rp = kwargs["retry_policy"]
            if isinstance(rp, RetryPolicy):
                rp = {"maxAttempts": rp.max_attempts, "initialDelay": rp.initial_delay,
                       "maxDelay": rp.max_delay, "backoffFactor": rp.backoff_factor}
            inp["retryPolicy"] = rp
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
        return _parse_destination(data["createDestination"])

    async def update(self, id: str, **kwargs: Any) -> Destination:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "url": "url", "status": "status",
                    "type": "type", "type_config": "typeConfig",
                    "timeout_ms": "timeoutMs", "rate_limit_rps": "rateLimitRps",
                    "headers": "headers", "auth_type": "authType",
                    "mtls_cert": "mtlsCert", "mtls_key": "mtlsKey",
                    "delivery_mode": "deliveryMode", "ordered": "ordered",
                    "output_format": "outputFormat"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "retry_policy" in kwargs and kwargs["retry_policy"] is not None:
            rp = kwargs["retry_policy"]
            if isinstance(rp, RetryPolicy):
                rp = {"maxAttempts": rp.max_attempts, "initialDelay": rp.initial_delay,
                       "maxDelay": rp.max_delay, "backoffFactor": rp.backoff_factor}
            inp["retryPolicy"] = rp
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
        return _parse_destination(data["updateDestination"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteDestination", False)

    async def rotate_secret(self, id: str) -> Destination:
        data = await self._t.execute(_ROTATE_SECRET_MUTATION, {"id": id})
        return _parse_destination(data["rotateDestinationSecret"])

    async def poll_deliveries(
        self, destination_id: str, cursor: str | None = None, limit: int | None = None,
    ) -> ListResult[Delivery]:
        v: dict[str, Any] = {"destinationId": destination_id}
        if cursor is not None:
            v["cursor"] = cursor
        if limit is not None:
            v["limit"] = limit
        data = await self._t.execute(_POLL_DELIVERIES_QUERY, v)
        conn = data["pollDeliveries"]
        return ListResult(
            nodes=[_parse_delivery(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def ack_deliveries(self, destination_id: str, delivery_ids: list[str]) -> int:
        data = await self._t.execute(_ACK_DELIVERIES_MUTATION, {"destinationId": destination_id, "deliveryIds": delivery_ids})
        return data.get("ackDeliveries", 0)

    async def regenerate_poll_api_key(self, destination_id: str) -> Destination:
        data = await self._t.execute(_REGENERATE_POLL_API_KEY_MUTATION, {"destinationId": destination_id})
        return _parse_destination(data["regeneratePollApiKey"])

    async def skip_dlq_entry(self, id: str) -> bool:
        data = await self._t.execute(_SKIP_DLQ_ENTRY_MUTATION, {"id": id})
        return data.get("skipDLQEntry", False)

    def iterate(self, **filters: Any) -> AsyncIterator[Destination]:
        return paginate_async(self.list, **filters)
