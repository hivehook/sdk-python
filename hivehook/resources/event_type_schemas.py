from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import EventTypeSchema, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_SCHEMA_FIELDS = "id eventType description schema example createdAt updatedAt"

_LIST_QUERY = """
query ListEventTypeSchemas($search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  eventTypeSchemas(search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _SCHEMA_FIELDS

_GET_QUERY = """
query GetEventTypeSchema($id: UUID!) {
  eventTypeSchema(id: $id) { %s }
}
""" % _SCHEMA_FIELDS

_CREATE_MUTATION = """
mutation CreateEventTypeSchema($input: CreateEventTypeSchemaInput!) {
  createEventTypeSchema(input: $input) { %s }
}
""" % _SCHEMA_FIELDS

_UPDATE_MUTATION = """
mutation UpdateEventTypeSchema($id: UUID!, $input: UpdateEventTypeSchemaInput!) {
  updateEventTypeSchema(id: $id, input: $input) { %s }
}
""" % _SCHEMA_FIELDS

_DELETE_MUTATION = """
mutation DeleteEventTypeSchema($id: UUID!) {
  deleteEventTypeSchema(id: $id)
}
"""


def _parse_event_type_schema(data: dict[str, Any]) -> EventTypeSchema:
    return EventTypeSchema(
        id=data.get("id", ""),
        event_type=data.get("eventType", ""),
        description=data.get("description", ""),
        schema=data.get("schema"),
        example=data.get("example"),
        created_at=data.get("createdAt", ""),
        updated_at=data.get("updatedAt", ""),
    )


class EventTypeSchemaService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[EventTypeSchema]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["eventTypeSchemas"]
        return ListResult(
            nodes=[_parse_event_type_schema(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> EventTypeSchema | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("eventTypeSchema")
        return _parse_event_type_schema(s) if s else None

    def create(
        self, event_type: str, description: str = "",
        schema: dict[str, Any] | None = None,
        example: dict[str, Any] | None = None,
    ) -> EventTypeSchema:
        inp: dict[str, Any] = {"eventType": event_type, "description": description}
        if schema is not None:
            inp["schema"] = schema
        if example is not None:
            inp["example"] = example
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_event_type_schema(data["createEventTypeSchema"])

    def update(self, id: str, **kwargs: Any) -> EventTypeSchema:
        inp: dict[str, Any] = {}
        key_map = {"event_type": "eventType", "description": "description",
                    "schema": "schema", "example": "example"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_event_type_schema(data["updateEventTypeSchema"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteEventTypeSchema", False)

    def iterate(self, **filters: Any) -> Iterator[EventTypeSchema]:
        return paginate(self.list, **filters)


class AsyncEventTypeSchemaService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[EventTypeSchema]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["eventTypeSchemas"]
        return ListResult(
            nodes=[_parse_event_type_schema(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> EventTypeSchema | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        s = data.get("eventTypeSchema")
        return _parse_event_type_schema(s) if s else None

    async def create(
        self, event_type: str, description: str = "",
        schema: dict[str, Any] | None = None,
        example: dict[str, Any] | None = None,
    ) -> EventTypeSchema:
        inp: dict[str, Any] = {"eventType": event_type, "description": description}
        if schema is not None:
            inp["schema"] = schema
        if example is not None:
            inp["example"] = example
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_event_type_schema(data["createEventTypeSchema"])

    async def update(self, id: str, **kwargs: Any) -> EventTypeSchema:
        inp: dict[str, Any] = {}
        key_map = {"event_type": "eventType", "description": "description",
                    "schema": "schema", "example": "example"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_event_type_schema(data["updateEventTypeSchema"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteEventTypeSchema", False)

    def iterate(self, **filters: Any) -> AsyncIterator[EventTypeSchema]:
        return paginate_async(self.list, **filters)
