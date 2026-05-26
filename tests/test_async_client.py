from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from hivehook import AsyncHivehookClient
from hivehook.errors import (
    AuthError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from hivehook.types import Source


def _run(coro):
    return asyncio.run(coro)


def _make_handler(state: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode() or "{}")
        query = body.get("query", "")
        variables = body.get("variables", {}) or {}
        auth = request.headers.get("Authorization", "")
        state["calls"] = state.get("calls", 0) + 1

        if state.get("force_status"):
            status = state.pop("force_status")
            extra_headers = state.pop("force_headers", {}) or {}
            extra_body = state.pop("force_body", {"errors": [{"message": "forced"}]})
            return httpx.Response(status, json=extra_body, headers=extra_headers)

        if state.get("rate_limit_first"):
            state["rate_limit_first"] = False
            return httpx.Response(
                429,
                json={"errors": [{"message": "rate limited"}]},
                headers={"Retry-After": "0"},
            )

        if state.get("server_error_first"):
            state["server_error_first"] = False
            return httpx.Response(
                503,
                json={"errors": [{"message": "service unavailable"}]},
            )

        if auth == "Bearer bad_key":
            return httpx.Response(
                200,
                json={"errors": [{"message": "unauthorized", "extensions": {"code": "UNAUTHORIZED"}}]},
            )

        if "sources" in query and "$id" not in query and "mutation" not in query:
            return httpx.Response(
                200,
                json={"data": {"sources": {
                    "nodes": [
                        {"id": "src-a", "name": "GH", "slug": "gh",
                         "providerType": "github", "status": "ACTIVE",
                         "rateLimitRps": 0, "createdAt": "2025-01-01T00:00:00Z"},
                    ],
                    "pageInfo": {"total": 1, "limit": 20, "offset": 0,
                                 "endCursor": None, "hasNextPage": False},
                }}},
            )

        if "source" in query and "$id" in query and "mutation" not in query:
            if variables.get("id") == "missing":
                return httpx.Response(
                    200,
                    json={"errors": [{"message": "source not found",
                                       "extensions": {"code": "NOT_FOUND"}}]},
                )
            return httpx.Response(
                200,
                json={"data": {"source": {
                    "id": "src-a", "name": "GH", "slug": "gh",
                    "providerType": "github", "status": "ACTIVE",
                    "rateLimitRps": 0, "createdAt": "2025-01-01T00:00:00Z",
                }}},
            )

        if "createSource" in query:
            inp = variables.get("input", {})
            return httpx.Response(
                200,
                json={"data": {"createSource": {
                    "id": "src-new", "name": inp.get("name", ""),
                    "slug": inp.get("slug", ""),
                    "providerType": inp.get("providerType", ""),
                    "status": "ACTIVE", "rateLimitRps": 0,
                    "createdAt": "2025-01-01T00:00:00Z",
                }}},
            )

        if "deleteSource" in query:
            return httpx.Response(200, json={"data": {"deleteSource": True}})

        return httpx.Response(200, json={"data": {}})

    return handler


def _client(state: dict, **kwargs) -> AsyncHivehookClient:
    transport = httpx.MockTransport(_make_handler(state))
    http_client = httpx.AsyncClient(transport=transport)
    return AsyncHivehookClient(
        api_key=kwargs.pop("api_key", "test_key"),
        base_url="http://mock",
        client=http_client,
        **kwargs,
    )


def test_async_list_sources():
    async def run():
        state: dict = {}
        client = _client(state)
        try:
            result = await client.sources.list()
            assert len(result.nodes) == 1
            assert isinstance(result.nodes[0], Source)
            assert result.nodes[0].slug == "gh"
        finally:
            await client.close()
    _run(run())


def test_async_get_source():
    async def run():
        state: dict = {}
        client = _client(state)
        try:
            src = await client.sources.get("src-a")
            assert src is not None
            assert src.id == "src-a"
        finally:
            await client.close()
    _run(run())


def test_async_create_source():
    async def run():
        state: dict = {}
        client = _client(state)
        try:
            src = await client.sources.create(
                name="New", slug="new", provider_type="generic",
            )
            assert src.id == "src-new"
            assert src.name == "New"
        finally:
            await client.close()
    _run(run())


def test_async_delete_source():
    async def run():
        state: dict = {}
        client = _client(state)
        try:
            ok = await client.sources.delete("src-a")
            assert ok is True
        finally:
            await client.close()
    _run(run())


def test_async_not_found():
    async def run():
        state: dict = {}
        client = _client(state)
        try:
            with pytest.raises(NotFoundError):
                await client.sources.get("missing")
        finally:
            await client.close()
    _run(run())


def test_async_auth_error():
    async def run():
        state: dict = {}
        client = _client(state, api_key="bad_key")
        try:
            with pytest.raises(AuthError):
                await client.sources.list()
        finally:
            await client.close()
    _run(run())


def test_async_rate_limit_error_no_retry():
    async def run():
        state: dict = {"force_status": 429, "force_headers": {"Retry-After": "1"},
                       "force_body": {"errors": [{"message": "rate limited"}]}}
        # max_retries=0 so it propagates immediately
        client = _client(state, max_retries=0)
        try:
            with pytest.raises(RateLimitError) as ei:
                await client.sources.list()
            assert ei.value.retry_after == 1.0
            assert ei.value.status_code == 429
        finally:
            await client.close()
    _run(run())


def test_async_server_error_no_retry():
    async def run():
        state: dict = {"force_status": 500,
                       "force_body": {"errors": [{"message": "boom"}]}}
        client = _client(state, max_retries=0)
        try:
            with pytest.raises(ServerError) as ei:
                await client.sources.list()
            assert ei.value.status_code == 500
        finally:
            await client.close()
    _run(run())


def test_async_rate_limit_retry_then_success():
    async def run():
        state: dict = {"rate_limit_first": True}
        client = _client(state, max_retries=2)
        try:
            result = await client.sources.list()
            assert len(result.nodes) == 1
            # We made 2 calls: one 429, one success
            assert state["calls"] == 2
        finally:
            await client.close()
    _run(run())


def test_async_server_error_retry_then_success():
    async def run():
        state: dict = {"server_error_first": True}
        client = _client(state, max_retries=2)
        try:
            result = await client.sources.list()
            assert len(result.nodes) == 1
            assert state["calls"] == 2
        finally:
            await client.close()
    _run(run())


def test_async_not_found_not_retried():
    async def run():
        state: dict = {}
        client = _client(state, max_retries=5)
        try:
            with pytest.raises(NotFoundError):
                await client.sources.get("missing")
            # No retry on not-found
            assert state["calls"] == 1
        finally:
            await client.close()
    _run(run())


def test_async_user_supplied_client_not_closed():
    async def run():
        state: dict = {}
        transport = httpx.MockTransport(_make_handler(state))
        http_client = httpx.AsyncClient(transport=transport)
        client = AsyncHivehookClient(
            api_key="k", base_url="http://mock", client=http_client,
        )
        await client.close()
        # User-supplied client should not be closed by close()
        assert not http_client.is_closed
        await http_client.aclose()
    _run(run())
