import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import pytest

from hivehook import HivehookClient
from hivehook.errors import NotFoundError
from hivehook.types import Transformation, TransformTestResult


class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        query = body.get("query", "")
        variables = body.get("variables", {})

        if "transformations" in query and "mutation" not in query and "$id" not in query:
            resp = {"data": {"transformations": {
                "nodes": [
                    {"id": "tf-1", "name": "Add Header", "description": "Adds auth header",
                     "code": "function transform(evt) { return evt; }",
                     "enabled": True, "failOpen": False, "timeoutMs": 1000,
                     "createdAt": "2025-01-01T00:00:00Z",
                     "updatedAt": "2025-01-01T00:00:00Z"},
                ],
                "pageInfo": {"total": 1, "limit": 20, "offset": 0,
                             "endCursor": None, "hasNextPage": False},
            }}}
        elif "transformation" in query and "$id" in query and "mutation" not in query:
            if variables.get("id") == "not-found":
                resp = {"errors": [{"message": "transformation not found",
                                    "extensions": {"code": "NOT_FOUND"}}]}
            else:
                resp = {"data": {"transformation": {
                    "id": "tf-1", "name": "Add Header", "description": "Adds auth header",
                    "code": "function transform(evt) { return evt; }",
                    "enabled": True, "failOpen": False, "timeoutMs": 1000,
                    "createdAt": "2025-01-01T00:00:00Z",
                    "updatedAt": "2025-01-01T00:00:00Z",
                }}}
        elif "createTransformation" in query:
            inp = variables.get("input", {})
            resp = {"data": {"createTransformation": {
                "id": "tf-new", "name": inp.get("name", ""),
                "description": inp.get("description", ""),
                "code": inp.get("code", ""),
                "enabled": True, "failOpen": inp.get("failOpen", False),
                "timeoutMs": inp.get("timeoutMs", 1000),
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-01T00:00:00Z",
            }}}
        elif "updateTransformation" in query:
            inp = variables.get("input", {})
            resp = {"data": {"updateTransformation": {
                "id": variables.get("id", "tf-1"),
                "name": inp.get("name", "Add Header"),
                "description": inp.get("description", "Adds auth header"),
                "code": inp.get("code", "function transform(evt) { return evt; }"),
                "enabled": inp.get("enabled", True),
                "failOpen": inp.get("failOpen", False),
                "timeoutMs": inp.get("timeoutMs", 1000),
                "createdAt": "2025-01-01T00:00:00Z",
                "updatedAt": "2025-01-02T00:00:00Z",
            }}}
        elif "deleteTransformation" in query:
            resp = {"data": {"deleteTransformation": True}}
        elif "testTransformation" in query:
            resp = {"data": {"testTransformation": {
                "success": True,
                "output": {"body": {"transformed": True}},
                "error": "",
                "durationMs": 12,
            }}}
        else:
            resp = {"data": {}}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode())

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def server():
    srv = HTTPServer(("127.0.0.1", 0), MockHandler)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()


@pytest.fixture
def client(server):
    return HivehookClient(api_key="test_key", base_url=server)


def test_list_transformations(client):
    result = client.transformations.list()
    assert len(result.nodes) == 1
    assert isinstance(result.nodes[0], Transformation)
    assert result.nodes[0].name == "Add Header"
    assert result.page_info.total == 1


def test_list_transformations_with_filters(client):
    result = client.transformations.list(enabled=True, search="header")
    assert len(result.nodes) == 1


def test_get_transformation(client):
    t = client.transformations.get("tf-1")
    assert t is not None
    assert t.id == "tf-1"
    assert t.name == "Add Header"
    assert t.description == "Adds auth header"
    assert t.enabled is True
    assert t.fail_open is False
    assert t.timeout_ms == 1000


def test_get_transformation_not_found(client):
    with pytest.raises(NotFoundError):
        client.transformations.get("not-found")


def test_create_transformation(client):
    t = client.transformations.create(
        name="Enrich", code="function transform(evt) { return evt; }",
        description="Enriches events", fail_open=True, timeout_ms=2000,
    )
    assert t.id == "tf-new"
    assert t.name == "Enrich"
    assert t.description == "Enriches events"


def test_update_transformation(client):
    t = client.transformations.update("tf-1", name="Updated", enabled=False)
    assert t.id == "tf-1"
    assert t.name == "Updated"
    assert t.updated_at == "2025-01-02T00:00:00Z"


def test_delete_transformation(client):
    result = client.transformations.delete("tf-1")
    assert result is True


def test_test_transformation(client):
    result = client.transformations.test(
        code="function transform(evt) { return evt; }",
        payload={"key": "value"},
        event_type="order.created",
        headers={"X-Custom": "test"},
    )
    assert isinstance(result, TransformTestResult)
    assert result.success is True
    assert result.output == {"body": {"transformed": True}}
    assert result.error == ""
    assert result.duration_ms == 12


def test_page_info(client):
    result = client.transformations.list()
    assert result.page_info.has_next_page is False
    assert result.page_info.limit == 20
