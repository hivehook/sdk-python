from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from hivehook.types import User, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars, paginate, paginate_async

_USER_FIELDS = """
    id organizationId email name role lastLoginAt createdAt updatedAt
"""

_LIST_QUERY = """
query ListUsers($organizationId: UUID, $search: String, $limit: Int, $offset: Int) {
  users(organizationId: $organizationId, search: $search, limit: $limit, offset: $offset) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _USER_FIELDS

_ME_QUERY = """
query Me {
  me { %s }
}
""" % _USER_FIELDS

_INVITE_MUTATION = """
mutation InviteUser($organizationId: UUID!, $input: InviteUserInput!) {
  inviteUser(organizationId: $organizationId, input: $input) { %s }
}
""" % _USER_FIELDS

_REMOVE_MUTATION = """
mutation RemoveUser($id: UUID!) {
  removeUser(id: $id)
}
"""

_UPDATE_ROLE_MUTATION = """
mutation UpdateUserRole($id: UUID!, $input: UpdateUserRoleInput!) {
  updateUserRole(id: $id, input: $input) { %s }
}
""" % _USER_FIELDS


def _parse_user(data: dict[str, Any]) -> User:
    return User(
        id=data.get("id", ""),
        organization_id=data.get("organizationId", ""),
        email=data.get("email", ""),
        name=data.get("name", ""),
        role=data.get("role", ""),
        last_login_at=data.get("lastLoginAt"),
        created_at=data.get("createdAt", ""),
        updated_at=data.get("updatedAt", ""),
    )


class UserService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, organization_id: str | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
    ) -> ListResult[User]:
        v = build_list_vars(limit=limit, offset=offset, search=search, organizationId=organization_id)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["users"]
        return ListResult(
            nodes=[_parse_user(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def me(self) -> User | None:
        data = self._t.execute(_ME_QUERY, {})
        u = data.get("me")
        return _parse_user(u) if u else None

    def invite(
        self, organization_id: str, email: str,
        name: str | None = None, role: str | None = None,
    ) -> User:
        inp: dict[str, Any] = {"email": email}
        if name is not None:
            inp["name"] = name
        if role is not None:
            inp["role"] = role
        data = self._t.execute(_INVITE_MUTATION, {"organizationId": organization_id, "input": inp})
        return _parse_user(data["inviteUser"])

    def remove(self, id: str) -> bool:
        data = self._t.execute(_REMOVE_MUTATION, {"id": id})
        return data.get("removeUser", False)

    def update_role(self, id: str, role: str) -> User:
        inp: dict[str, Any] = {"role": role}
        data = self._t.execute(_UPDATE_ROLE_MUTATION, {"id": id, "input": inp})
        return _parse_user(data["updateUserRole"])

    def iterate(self, **filters: Any) -> Iterator[User]:
        return paginate(self.list, **filters)


class AsyncUserService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, organization_id: str | None = None,
        search: str | None = None,
        limit: int | None = None, offset: int | None = None,
    ) -> ListResult[User]:
        v = build_list_vars(limit=limit, offset=offset, search=search, organizationId=organization_id)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["users"]
        return ListResult(
            nodes=[_parse_user(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def me(self) -> User | None:
        data = await self._t.execute(_ME_QUERY, {})
        u = data.get("me")
        return _parse_user(u) if u else None

    async def invite(
        self, organization_id: str, email: str,
        name: str | None = None, role: str | None = None,
    ) -> User:
        inp: dict[str, Any] = {"email": email}
        if name is not None:
            inp["name"] = name
        if role is not None:
            inp["role"] = role
        data = await self._t.execute(_INVITE_MUTATION, {"organizationId": organization_id, "input": inp})
        return _parse_user(data["inviteUser"])

    async def remove(self, id: str) -> bool:
        data = await self._t.execute(_REMOVE_MUTATION, {"id": id})
        return data.get("removeUser", False)

    async def update_role(self, id: str, role: str) -> User:
        inp: dict[str, Any] = {"role": role}
        data = await self._t.execute(_UPDATE_ROLE_MUTATION, {"id": id, "input": inp})
        return _parse_user(data["updateUserRole"])

    def iterate(self, **filters: Any) -> AsyncIterator[User]:
        return paginate_async(self.list, **filters)
