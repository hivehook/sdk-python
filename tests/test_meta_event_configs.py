import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from hivehook import HivehookClient, MetaEventConfig, StreamEntry


class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        query = body.get("query", "")
        vars = body.get("variables", {})

        if "metaEventConfigs" in query:
            resp = {"data": {"metaEventConfigs": {
                "nodes": [{
                    "id": "me-1", "name": "DLQ alerts", "url": "https://hooks/x",
                    "signingSecret": "whsec", "eventTypes": ["delivery.failed"],
                    "enabled": True, "createdAt": "2025-01-01T00:00:00Z",
                }],
                "pageInfo": {"total": 1, "limit": 50, "offset": 0, "hasNextPage": False},
            }}}
        elif "metaEventConfig(" in query:
            resp = {"data": {"metaEventConfig": {
                "id": vars["id"], "name": "x", "url": "https://x",
                "signingSecret": "s", "eventTypes": [], "enabled": True,
                "createdAt": "2025-01-01T00:00:00Z",
            }}}
        elif "createMetaEventConfig" in query:
            inp = vars["input"]
            resp = {"data": {"createMetaEventConfig": {
                "id": "me-new", "name": inp["name"], "url": inp["url"],
                "signingSecret": "s", "eventTypes": inp["eventTypes"], "enabled": True,
                "createdAt": "2025-01-01T00:00:00Z",
            }}}
        elif "updateMetaEventConfig" in query:
            inp = vars["input"]
            resp = {"data": {"updateMetaEventConfig": {
                "id": vars["id"], "name": inp.get("name", "old"),
                "url": "https://x", "signingSecret": "s", "eventTypes": [],
                "enabled": True, "createdAt": "2025-01-01T00:00:00Z",
            }}}
        elif "deleteMetaEventConfig" in query:
            resp = {"data": {"deleteMetaEventConfig": True}}
        elif "streamEntries" in query:
            resp = {"data": {"streamEntries": {
                "nodes": [{
                    "id": "se-1", "streamId": vars["streamId"], "sequence": 101,
                    "messageId": None, "eventType": "user.created",
                    "payload": "eyJrIjoidiJ9", "createdAt": "2025-01-01T00:00:00Z",
                }],
                "pageInfo": {"total": 1, "limit": 50, "offset": 0, "hasNextPage": False},
            }}}
        else:
            resp = {"errors": [{"message": "unhandled query"}]}

        body = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


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


def test_list(client):
    r = client.meta_event_configs.list()
    assert len(r.nodes) == 1
    assert isinstance(r.nodes[0], MetaEventConfig)
    assert r.nodes[0].name == "DLQ alerts"


def test_get(client):
    c = client.meta_event_configs.get("me-7")
    assert c is not None
    assert c.id == "me-7"


def test_create(client):
    c = client.meta_event_configs.create(name="new", url="https://new", event_types=["source.created"])
    assert c.id == "me-new"


def test_update(client):
    c = client.meta_event_configs.update("me-1", name="renamed")
    assert c.name == "renamed"


def test_delete(client):
    assert client.meta_event_configs.delete("me-1") is True


def test_stream_entries(client):
    r = client.streams.entries("stream-1")
    assert len(r.nodes) == 1
    assert isinstance(r.nodes[0], StreamEntry)
    assert r.nodes[0].sequence == 101
