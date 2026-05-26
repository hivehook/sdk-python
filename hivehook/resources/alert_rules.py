from __future__ import annotations

from typing import Any

from hivehook.types import AlertRule, EmailAlertConfig, SlackAlertConfig, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars

_ALERT_FIELDS = "id name conditionType threshold webhookUrl channel emailConfig { to subjectTemplate } slackConfig { webhookUrl channel } cooldown enabled createdAt"

_LIST_QUERY = """
query ListAlertRules($enabled: Boolean, $search: String,
                      $limit: Int, $offset: Int, $after: String, $first: Int) {
  alertRules(enabled: $enabled, search: $search,
             limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _ALERT_FIELDS

_GET_QUERY = """
query GetAlertRule($id: UUID!) {
  alertRule(id: $id) { %s }
}
""" % _ALERT_FIELDS

_CREATE_MUTATION = """
mutation CreateAlertRule($input: CreateAlertRuleInput!) {
  createAlertRule(input: $input) { %s }
}
""" % _ALERT_FIELDS

_UPDATE_MUTATION = """
mutation UpdateAlertRule($id: UUID!, $input: UpdateAlertRuleInput!) {
  updateAlertRule(id: $id, input: $input) { %s }
}
""" % _ALERT_FIELDS

_DELETE_MUTATION = """
mutation DeleteAlertRule($id: UUID!) {
  deleteAlertRule(id: $id)
}
"""

_TEST_MUTATION = """
mutation TestAlertRule($id: UUID!) {
  testAlertRule(id: $id)
}
"""


def _parse_email_config(data: dict[str, Any] | None) -> EmailAlertConfig | None:
    if data is None:
        return None
    return EmailAlertConfig(
        to=data.get("to", []),
        subject_template=data.get("subjectTemplate"),
    )


def _parse_slack_config(data: dict[str, Any] | None) -> SlackAlertConfig | None:
    if data is None:
        return None
    return SlackAlertConfig(
        webhook_url=data.get("webhookUrl", ""),
        channel=data.get("channel"),
    )


def _parse_alert_rule(data: dict[str, Any]) -> AlertRule:
    return AlertRule(
        id=data.get("id", ""),
        name=data.get("name", ""),
        condition_type=data.get("conditionType", ""),
        threshold=data.get("threshold", 0),
        webhook_url=data.get("webhookUrl", ""),
        channel=data.get("channel", "WEBHOOK"),
        email_config=_parse_email_config(data.get("emailConfig")),
        slack_config=_parse_slack_config(data.get("slackConfig")),
        cooldown=data.get("cooldown", ""),
        enabled=data.get("enabled", True),
        created_at=data.get("createdAt", ""),
    )


class AlertRuleService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, enabled: bool | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[AlertRule]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            enabled=enabled, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["alertRules"]
        return ListResult(
            nodes=[_parse_alert_rule(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> AlertRule | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        r = data.get("alertRule")
        return _parse_alert_rule(r) if r else None

    def create(
        self, name: str, condition_type: str, threshold: int,
        webhook_url: str | None = None, cooldown: str = "5m", enabled: bool = True,
        channel: str | None = None, email_config: dict[str, Any] | None = None,
        slack_config: dict[str, Any] | None = None,
    ) -> AlertRule:
        inp: dict[str, Any] = {
            "name": name, "conditionType": condition_type,
            "threshold": threshold, "cooldown": cooldown, "enabled": enabled,
        }
        if webhook_url is not None:
            inp["webhookUrl"] = webhook_url
        if channel is not None:
            inp["channel"] = channel
        if email_config is not None:
            inp["emailConfig"] = email_config
        if slack_config is not None:
            inp["slackConfig"] = slack_config
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_alert_rule(data["createAlertRule"])

    def update(self, id: str, **kwargs: Any) -> AlertRule:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "condition_type": "conditionType",
                    "threshold": "threshold", "webhook_url": "webhookUrl",
                    "channel": "channel", "email_config": "emailConfig",
                    "slack_config": "slackConfig",
                    "cooldown": "cooldown", "enabled": "enabled"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_alert_rule(data["updateAlertRule"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteAlertRule", False)

    def test(self, id: str) -> bool:
        data = self._t.execute(_TEST_MUTATION, {"id": id})
        return data.get("testAlertRule", False)


class AsyncAlertRuleService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, enabled: bool | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[AlertRule]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            enabled=enabled, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["alertRules"]
        return ListResult(
            nodes=[_parse_alert_rule(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> AlertRule | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        r = data.get("alertRule")
        return _parse_alert_rule(r) if r else None

    async def create(
        self, name: str, condition_type: str, threshold: int,
        webhook_url: str | None = None, cooldown: str = "5m", enabled: bool = True,
        channel: str | None = None, email_config: dict[str, Any] | None = None,
        slack_config: dict[str, Any] | None = None,
    ) -> AlertRule:
        inp: dict[str, Any] = {
            "name": name, "conditionType": condition_type,
            "threshold": threshold, "cooldown": cooldown, "enabled": enabled,
        }
        if webhook_url is not None:
            inp["webhookUrl"] = webhook_url
        if channel is not None:
            inp["channel"] = channel
        if email_config is not None:
            inp["emailConfig"] = email_config
        if slack_config is not None:
            inp["slackConfig"] = slack_config
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_alert_rule(data["createAlertRule"])

    async def update(self, id: str, **kwargs: Any) -> AlertRule:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "condition_type": "conditionType",
                    "threshold": "threshold", "webhook_url": "webhookUrl",
                    "channel": "channel", "email_config": "emailConfig",
                    "slack_config": "slackConfig",
                    "cooldown": "cooldown", "enabled": "enabled"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_alert_rule(data["updateAlertRule"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteAlertRule", False)

    async def test(self, id: str) -> bool:
        data = await self._t.execute(_TEST_MUTATION, {"id": id})
        return data.get("testAlertRule", False)
