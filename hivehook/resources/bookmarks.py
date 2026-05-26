from __future__ import annotations

from typing import Any

from hivehook.types import Bookmark, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars

_BOOKMARK_FIELDS = "id eventId name notes createdAt"

_LIST_QUERY = """
query ListBookmarks($eventId: UUID, $search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  bookmarks(eventId: $eventId, search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _BOOKMARK_FIELDS

_GET_QUERY = """
query GetBookmark($id: UUID!) {
  bookmark(id: $id) { %s }
}
""" % _BOOKMARK_FIELDS

_CREATE_MUTATION = """
mutation CreateBookmark($eventId: UUID!, $name: String, $notes: String) {
  createBookmark(eventId: $eventId, name: $name, notes: $notes) { %s }
}
""" % _BOOKMARK_FIELDS

_DELETE_MUTATION = """
mutation DeleteBookmark($id: UUID!) {
  deleteBookmark(id: $id)
}
"""


def _parse_bookmark(data: dict[str, Any]) -> Bookmark:
    return Bookmark(
        id=data.get("id", ""),
        event_id=data.get("eventId", ""),
        name=data.get("name", ""),
        notes=data.get("notes", ""),
        created_at=data.get("createdAt", ""),
    )


class BookmarkService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, event_id: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Bookmark]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first, eventId=event_id, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["bookmarks"]
        return ListResult(
            nodes=[_parse_bookmark(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Bookmark | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        b = data.get("bookmark")
        return _parse_bookmark(b) if b else None

    def create(self, event_id: str, name: str, notes: str = "") -> Bookmark:
        data = self._t.execute(_CREATE_MUTATION, {"eventId": event_id, "name": name, "notes": notes})
        return _parse_bookmark(data["createBookmark"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteBookmark", False)


class AsyncBookmarkService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, event_id: str | None = None, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Bookmark]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first, eventId=event_id, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["bookmarks"]
        return ListResult(
            nodes=[_parse_bookmark(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Bookmark | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        b = data.get("bookmark")
        return _parse_bookmark(b) if b else None

    async def create(self, event_id: str, name: str, notes: str = "") -> Bookmark:
        data = await self._t.execute(_CREATE_MUTATION, {"eventId": event_id, "name": name, "notes": notes})
        return _parse_bookmark(data["createBookmark"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteBookmark", False)
