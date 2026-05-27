from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import AuditLog, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_AUDIT_LOG_FIELDS = """
    id actorType actorId actorName action resourceType resourceId
    orgId ipAddress userAgent details createdAt
"""

_LIST_QUERY = """
query ListAuditLogs($actorType: String, $resourceType: String, $resourceId: UUID, $action: String, $since: Time, $until: Time, $search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  auditLogs(actorType: $actorType, resourceType: $resourceType, resourceId: $resourceId, action: $action, since: $since, until: $until, search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _AUDIT_LOG_FIELDS

_GET_QUERY = """
query GetAuditLog($id: UUID!) {
  auditLog(id: $id) { %s }
}
""" % _AUDIT_LOG_FIELDS


def _parse_audit_log(data: dict[str, Any]) -> AuditLog:
    return AuditLog(
        id=data.get("id", ""),
        actor_type=data.get("actorType", ""),
        actor_id=data.get("actorId", ""),
        actor_name=data.get("actorName", ""),
        action=data.get("action", ""),
        resource_type=data.get("resourceType", ""),
        resource_id=data.get("resourceId", ""),
        org_id=data.get("orgId", ""),
        ip_address=data.get("ipAddress", ""),
        user_agent=data.get("userAgent", ""),
        details=data.get("details"),
        created_at=data.get("createdAt", ""),
    )


class AuditLogService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, actor_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        since: str | None = None,
        until: str | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[AuditLog]:
        v = build_list_vars(
            limit=limit, offset=offset, after=after, first=first,
            search=search, actorType=actor_type, resourceType=resource_type,
            resourceId=resource_id, action=action, since=since, until=until,
        )
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["auditLogs"]
        return ListResult(
            nodes=[_parse_audit_log(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> AuditLog | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        a = data.get("auditLog")
        return _parse_audit_log(a) if a else None

    def iterate(self, **filters: Any) -> Iterator[AuditLog]:
        return paginate(self.list, **filters)


class AsyncAuditLogService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, actor_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        since: str | None = None,
        until: str | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[AuditLog]:
        v = build_list_vars(
            limit=limit, offset=offset, after=after, first=first,
            search=search, actorType=actor_type, resourceType=resource_type,
            resourceId=resource_id, action=action, since=since, until=until,
        )
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["auditLogs"]
        return ListResult(
            nodes=[_parse_audit_log(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> AuditLog | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        a = data.get("auditLog")
        return _parse_audit_log(a) if a else None

    def iterate(self, **filters: Any) -> AsyncIterator[AuditLog]:
        return paginate_async(self.list, **filters)
