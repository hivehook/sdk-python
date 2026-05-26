from __future__ import annotations

from typing import Any

from hivehook.types import Subscription, ListResult, FilterConfig, TransformConfig, FilterRule, BodyMatchRule
from hivehook.resources._base import parse_page_info, build_list_vars

_SUB_FIELDS = """
    id name sourceId destinationId
    filterConfig {
      eventTypes regex
      bodyMatch { path value operator }
      rules { path operator value rules { path operator value } }
    }
    transformConfig { envelope headers }
    enabled createdAt
"""

_LIST_QUERY = """
query ListSubscriptions($sourceId: UUID, $destinationId: UUID, $enabled: Boolean,
                         $search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  subscriptions(sourceId: $sourceId, destinationId: $destinationId, enabled: $enabled,
                search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _SUB_FIELDS

_GET_QUERY = """
query GetSubscription($id: UUID!) {
  subscription(id: $id) { %s }
}
""" % _SUB_FIELDS

_CREATE_MUTATION = """
mutation CreateSubscription($input: CreateSubscriptionInput!) {
  createSubscription(input: $input) { %s }
}
""" % _SUB_FIELDS

_UPDATE_MUTATION = """
mutation UpdateSubscription($id: UUID!, $input: UpdateSubscriptionInput!) {
  updateSubscription(id: $id, input: $input) { %s }
}
""" % _SUB_FIELDS

_DELETE_MUTATION = """
mutation DeleteSubscription($id: UUID!) {
  deleteSubscription(id: $id)
}
"""


def _parse_filter_rule(data: dict[str, Any]) -> FilterRule:
    sub_rules = None
    if data.get("rules"):
        sub_rules = [_parse_filter_rule(r) for r in data["rules"]]
    return FilterRule(
        operator=data.get("operator", ""),
        path=data.get("path"),
        value=data.get("value"),
        rules=sub_rules,
    )


def _parse_filter_config(data: dict[str, Any] | None) -> FilterConfig | None:
    if not data:
        return None
    body_match = None
    if data.get("bodyMatch"):
        body_match = [
            BodyMatchRule(path=b.get("path", ""), value=b.get("value", ""), operator=b.get("operator", ""))
            for b in data["bodyMatch"]
        ]
    rules = None
    if data.get("rules"):
        rules = [_parse_filter_rule(r) for r in data["rules"]]
    return FilterConfig(
        event_types=data.get("eventTypes"),
        regex=data.get("regex"),
        body_match=body_match,
        rules=rules,
    )


def _parse_transform_config(data: dict[str, Any] | None) -> TransformConfig | None:
    if not data:
        return None
    return TransformConfig(
        envelope=data.get("envelope", False),
        headers=data.get("headers"),
    )


def _parse_subscription(data: dict[str, Any]) -> Subscription:
    return Subscription(
        id=data.get("id", ""),
        name=data.get("name", ""),
        source_id=data.get("sourceId", ""),
        destination_id=data.get("destinationId", ""),
        filter_config=_parse_filter_config(data.get("filterConfig")),
        transform_config=_parse_transform_config(data.get("transformConfig")),
        enabled=data.get("enabled", True),
        created_at=data.get("createdAt", ""),
    )


def _build_filter_config_input(fc: FilterConfig) -> dict[str, Any]:
    d: dict[str, Any] = {}
    if fc.event_types is not None:
        d["eventTypes"] = fc.event_types
    if fc.regex is not None:
        d["regex"] = fc.regex
    if fc.body_match is not None:
        d["bodyMatch"] = [{"path": b.path, "value": b.value, "operator": b.operator} for b in fc.body_match]
    if fc.rules is not None:
        d["rules"] = [_build_filter_rule_input(r) for r in fc.rules]
    return d


def _build_filter_rule_input(r: FilterRule) -> dict[str, Any]:
    d: dict[str, Any] = {"operator": r.operator}
    if r.path is not None:
        d["path"] = r.path
    if r.value is not None:
        d["value"] = r.value
    if r.rules is not None:
        d["rules"] = [_build_filter_rule_input(sub) for sub in r.rules]
    return d


class SubscriptionService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, source_id: str | None = None, destination_id: str | None = None,
        enabled: bool | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Subscription]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            sourceId=source_id, destinationId=destination_id,
                            enabled=enabled, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["subscriptions"]
        return ListResult(
            nodes=[_parse_subscription(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Subscription | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("subscription")
        return _parse_subscription(s) if s else None

    def create(
        self, name: str, source_id: str, destination_id: str,
        filter_config: FilterConfig | None = None,
        transform_config: TransformConfig | None = None,
        enabled: bool = True,
    ) -> Subscription:
        inp: dict[str, Any] = {
            "name": name, "sourceId": source_id, "destinationId": destination_id,
            "enabled": enabled,
        }
        if filter_config is not None:
            inp["filterConfig"] = _build_filter_config_input(filter_config)
        if transform_config is not None:
            tc: dict[str, Any] = {"envelope": transform_config.envelope}
            if transform_config.headers is not None:
                tc["headers"] = transform_config.headers
            inp["transformConfig"] = tc
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_subscription(data["createSubscription"])

    def update(self, id: str, **kwargs: Any) -> Subscription:
        inp: dict[str, Any] = {}
        for py_key, gql_key in [("name", "name"), ("enabled", "enabled")]:
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "filter_config" in kwargs and kwargs["filter_config"] is not None:
            inp["filterConfig"] = _build_filter_config_input(kwargs["filter_config"])
        if "transform_config" in kwargs and kwargs["transform_config"] is not None:
            tc = kwargs["transform_config"]
            d: dict[str, Any] = {"envelope": tc.envelope}
            if tc.headers is not None:
                d["headers"] = tc.headers
            inp["transformConfig"] = d
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_subscription(data["updateSubscription"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteSubscription", False)


class AsyncSubscriptionService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, source_id: str | None = None, destination_id: str | None = None,
        enabled: bool | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Subscription]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            sourceId=source_id, destinationId=destination_id,
                            enabled=enabled, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["subscriptions"]
        return ListResult(
            nodes=[_parse_subscription(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Subscription | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("subscription")
        return _parse_subscription(s) if s else None

    async def create(
        self, name: str, source_id: str, destination_id: str,
        filter_config: FilterConfig | None = None,
        transform_config: TransformConfig | None = None,
        enabled: bool = True,
    ) -> Subscription:
        inp: dict[str, Any] = {
            "name": name, "sourceId": source_id, "destinationId": destination_id,
            "enabled": enabled,
        }
        if filter_config is not None:
            inp["filterConfig"] = _build_filter_config_input(filter_config)
        if transform_config is not None:
            tc: dict[str, Any] = {"envelope": transform_config.envelope}
            if transform_config.headers is not None:
                tc["headers"] = transform_config.headers
            inp["transformConfig"] = tc
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_subscription(data["createSubscription"])

    async def update(self, id: str, **kwargs: Any) -> Subscription:
        inp: dict[str, Any] = {}
        for py_key, gql_key in [("name", "name"), ("enabled", "enabled")]:
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        if "filter_config" in kwargs and kwargs["filter_config"] is not None:
            inp["filterConfig"] = _build_filter_config_input(kwargs["filter_config"])
        if "transform_config" in kwargs and kwargs["transform_config"] is not None:
            tc = kwargs["transform_config"]
            d: dict[str, Any] = {"envelope": tc.envelope}
            if tc.headers is not None:
                d["headers"] = tc.headers
            inp["transformConfig"] = d
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_subscription(data["updateSubscription"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteSubscription", False)
