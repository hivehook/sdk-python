from __future__ import annotations

import base64
from typing import Any, AsyncIterator, Iterator

from hivehook.types import Message, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_MSG_FIELDS = "id applicationId eventType payload idempotencyKey status createdAt"

_LIST_QUERY = """
query ListMessages($applicationId: UUID, $eventType: String, $status: MessageStatus,
                    $search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  messages(applicationId: $applicationId, eventType: $eventType, status: $status,
           search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _MSG_FIELDS

_GET_QUERY = """
query GetMessage($id: UUID!) {
  message(id: $id) { %s }
}
""" % _MSG_FIELDS

_SEND_MUTATION = """
mutation SendMessage($input: SendMessageInput!) {
  sendMessage(input: $input) { %s }
}
""" % _MSG_FIELDS


def _parse_message(data: dict[str, Any]) -> Message:
    return Message(
        id=data.get("id", ""),
        application_id=data.get("applicationId", ""),
        event_type=data.get("eventType", ""),
        payload=data.get("payload"),
        idempotency_key=data.get("idempotencyKey", ""),
        status=data.get("status", ""),
        created_at=data.get("createdAt", ""),
    )


class MessageService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, application_id: str | None = None, event_type: str | None = None,
        status: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Message]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            applicationId=application_id, eventType=event_type,
                            status=status, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["messages"]
        return ListResult(
            nodes=[_parse_message(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Message | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        m = data.get("message")
        return _parse_message(m) if m else None

    def send(
        self, application_id: str, event_type: str, payload: str | bytes,
        idempotency_key: str = "",
    ) -> Message:
        if isinstance(payload, str):
            payload_b64 = base64.b64encode(payload.encode()).decode()
        else:
            payload_b64 = base64.b64encode(payload).decode()
        inp: dict[str, Any] = {
            "applicationId": application_id,
            "eventType": event_type,
            "payload": payload_b64,
        }
        if idempotency_key:
            inp["idempotencyKey"] = idempotency_key
        data = self._t.execute(_SEND_MUTATION, {"input": inp})
        return _parse_message(data["sendMessage"])

    def iterate(self, **filters: Any) -> Iterator[Message]:
        return paginate(self.list, **filters)


class AsyncMessageService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, application_id: str | None = None, event_type: str | None = None,
        status: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Message]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first,
                            applicationId=application_id, eventType=event_type,
                            status=status, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["messages"]
        return ListResult(
            nodes=[_parse_message(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Message | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        m = data.get("message")
        return _parse_message(m) if m else None

    async def send(
        self, application_id: str, event_type: str, payload: str | bytes,
        idempotency_key: str = "",
    ) -> Message:
        if isinstance(payload, str):
            payload_b64 = base64.b64encode(payload.encode()).decode()
        else:
            payload_b64 = base64.b64encode(payload).decode()
        inp: dict[str, Any] = {
            "applicationId": application_id,
            "eventType": event_type,
            "payload": payload_b64,
        }
        if idempotency_key:
            inp["idempotencyKey"] = idempotency_key
        data = await self._t.execute(_SEND_MUTATION, {"input": inp})
        return _parse_message(data["sendMessage"])

    def iterate(self, **filters: Any) -> AsyncIterator[Message]:
        return paginate_async(self.list, **filters)
