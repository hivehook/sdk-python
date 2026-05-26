from __future__ import annotations

from typing import Any

from hivehook.types import Transformation, TransformTestResult, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars

_TRANSFORM_FIELDS = "id name description code enabled failOpen timeoutMs createdAt updatedAt"

_TEST_RESULT_FIELDS = "success output error durationMs"

_LIST_QUERY = """
query ListTransformations($enabled: Boolean, $search: String,
                           $after: String, $first: Int) {
  transformations(enabled: $enabled, search: $search,
                  after: $after, first: $first) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _TRANSFORM_FIELDS

_GET_QUERY = """
query GetTransformation($id: UUID!) {
  transformation(id: $id) { %s }
}
""" % _TRANSFORM_FIELDS

_CREATE_MUTATION = """
mutation CreateTransformation($input: CreateTransformationInput!) {
  createTransformation(input: $input) { %s }
}
""" % _TRANSFORM_FIELDS

_UPDATE_MUTATION = """
mutation UpdateTransformation($id: UUID!, $input: UpdateTransformationInput!) {
  updateTransformation(id: $id, input: $input) { %s }
}
""" % _TRANSFORM_FIELDS

_DELETE_MUTATION = """
mutation DeleteTransformation($id: UUID!) {
  deleteTransformation(id: $id)
}
"""

_TEST_MUTATION = """
mutation TestTransformation($input: TestTransformationInput!) {
  testTransformation(input: $input) { %s }
}
""" % _TEST_RESULT_FIELDS


def _parse_transformation(data: dict[str, Any]) -> Transformation:
    return Transformation(
        id=data.get("id", ""),
        name=data.get("name", ""),
        description=data.get("description", ""),
        code=data.get("code", ""),
        enabled=data.get("enabled", True),
        fail_open=data.get("failOpen", False),
        timeout_ms=data.get("timeoutMs", 0),
        created_at=data.get("createdAt", ""),
        updated_at=data.get("updatedAt", ""),
    )


def _parse_test_result(data: dict[str, Any]) -> TransformTestResult:
    return TransformTestResult(
        success=data.get("success", False),
        output=data.get("output"),
        error=data.get("error", ""),
        duration_ms=data.get("durationMs", 0),
    )


class TransformationService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, enabled: bool | None = None, search: str | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Transformation]:
        v = build_list_vars(after=after, first=first,
                            enabled=enabled, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["transformations"]
        return ListResult(
            nodes=[_parse_transformation(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Transformation | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        t = data.get("transformation")
        return _parse_transformation(t) if t else None

    def create(
        self, name: str, code: str,
        description: str | None = None,
        fail_open: bool | None = None,
        timeout_ms: int | None = None,
    ) -> Transformation:
        inp: dict[str, Any] = {"name": name, "code": code}
        if description is not None:
            inp["description"] = description
        if fail_open is not None:
            inp["failOpen"] = fail_open
        if timeout_ms is not None:
            inp["timeoutMs"] = timeout_ms
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_transformation(data["createTransformation"])

    def update(self, id: str, **kwargs: Any) -> Transformation:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "description": "description", "code": "code",
                    "enabled": "enabled", "fail_open": "failOpen",
                    "timeout_ms": "timeoutMs"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_transformation(data["updateTransformation"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteTransformation", False)

    def test(
        self, code: str, payload: dict[str, Any],
        event_type: str | None = None,
        headers: dict[str, Any] | None = None,
    ) -> TransformTestResult:
        inp: dict[str, Any] = {"code": code, "payload": payload}
        if event_type is not None:
            inp["eventType"] = event_type
        if headers is not None:
            inp["headers"] = headers
        data = self._t.execute(_TEST_MUTATION, {"input": inp})
        return _parse_test_result(data["testTransformation"])


class AsyncTransformationService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, enabled: bool | None = None, search: str | None = None,
        after: str | None = None, first: int | None = None,
    ) -> ListResult[Transformation]:
        v = build_list_vars(after=after, first=first,
                            enabled=enabled, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["transformations"]
        return ListResult(
            nodes=[_parse_transformation(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Transformation | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        t = data.get("transformation")
        return _parse_transformation(t) if t else None

    async def create(
        self, name: str, code: str,
        description: str | None = None,
        fail_open: bool | None = None,
        timeout_ms: int | None = None,
    ) -> Transformation:
        inp: dict[str, Any] = {"name": name, "code": code}
        if description is not None:
            inp["description"] = description
        if fail_open is not None:
            inp["failOpen"] = fail_open
        if timeout_ms is not None:
            inp["timeoutMs"] = timeout_ms
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_transformation(data["createTransformation"])

    async def update(self, id: str, **kwargs: Any) -> Transformation:
        inp: dict[str, Any] = {}
        key_map = {"name": "name", "description": "description", "code": "code",
                    "enabled": "enabled", "fail_open": "failOpen",
                    "timeout_ms": "timeoutMs"}
        for py_key, gql_key in key_map.items():
            if py_key in kwargs:
                inp[gql_key] = kwargs[py_key]
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_transformation(data["updateTransformation"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteTransformation", False)

    async def test(
        self, code: str, payload: dict[str, Any],
        event_type: str | None = None,
        headers: dict[str, Any] | None = None,
    ) -> TransformTestResult:
        inp: dict[str, Any] = {"code": code, "payload": payload}
        if event_type is not None:
            inp["eventType"] = event_type
        if headers is not None:
            inp["headers"] = headers
        data = await self._t.execute(_TEST_MUTATION, {"input": inp})
        return _parse_test_result(data["testTransformation"])
