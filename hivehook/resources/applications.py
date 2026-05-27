from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import Application, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_APP_FIELDS = "id name uid createdAt"

_LIST_QUERY = """
query ListApplications($search: String, $limit: Int, $offset: Int, $after: String, $first: Int) {
  applications(search: $search, limit: $limit, offset: $offset, after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _APP_FIELDS

_GET_QUERY = """
query GetApplication($id: UUID!) {
  application(id: $id) { %s }
}
""" % _APP_FIELDS

_CREATE_MUTATION = """
mutation CreateApplication($input: CreateApplicationInput!) {
  createApplication(input: $input) { %s }
}
""" % _APP_FIELDS

_UPDATE_MUTATION = """
mutation UpdateApplication($id: UUID!, $input: UpdateApplicationInput!) {
  updateApplication(id: $id, input: $input) { %s }
}
""" % _APP_FIELDS

_DELETE_MUTATION = """
mutation DeleteApplication($id: UUID!) {
  deleteApplication(id: $id)
}
"""


def _parse_application(data: dict[str, Any]) -> Application:
    return Application(
        id=data.get("id", ""),
        name=data.get("name", ""),
        uid=data.get("uid", ""),
        created_at=data.get("createdAt", ""),
    )


class ApplicationService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Application]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["applications"]
        return ListResult(
            nodes=[_parse_application(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Application | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        a = data.get("application")
        return _parse_application(a) if a else None

    def create(self, name: str, uid: str = "") -> Application:
        inp: dict[str, Any] = {"name": name}
        if uid:
            inp["uid"] = uid
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_application(data["createApplication"])

    def update(self, id: str, **kwargs: Any) -> Application:
        inp: dict[str, Any] = {}
        if "name" in kwargs:
            inp["name"] = kwargs["name"]
        if "uid" in kwargs:
            inp["uid"] = kwargs["uid"]
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_application(data["updateApplication"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteApplication", False)

    def iterate(self, **filters: Any) -> Iterator[Application]:
        return paginate(self.list, **filters)


class AsyncApplicationService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Application]:
        v = build_list_vars(limit=limit, offset=offset, after=after, first=first, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["applications"]
        return ListResult(
            nodes=[_parse_application(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Application | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        a = data.get("application")
        return _parse_application(a) if a else None

    async def create(self, name: str, uid: str = "") -> Application:
        inp: dict[str, Any] = {"name": name}
        if uid:
            inp["uid"] = uid
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_application(data["createApplication"])

    async def update(self, id: str, **kwargs: Any) -> Application:
        inp: dict[str, Any] = {}
        if "name" in kwargs:
            inp["name"] = kwargs["name"]
        if "uid" in kwargs:
            inp["uid"] = kwargs["uid"]
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_application(data["updateApplication"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteApplication", False)

    def iterate(self, **filters: Any) -> AsyncIterator[Application]:
        return paginate_async(self.list, **filters)
