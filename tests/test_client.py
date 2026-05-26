import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

import pytest

from hivehook import HivehookClient
from hivehook.errors import NotFoundError, AuthError
from hivehook.types import Source, SystemStatus


class MockHandler(BaseHTTPRequestHandler):
    response_data = {}

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        query = body.get("query", "")

        auth = self.headers.get("Authorization", "")

        if auth == "Bearer bad_key":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {"errors": [{"message": "unauthorized", "extensions": {"code": "UNAUTHORIZED"}}]}
            self.wfile.write(json.dumps(resp).encode())
            return

        if "GetStatus" in query:
            resp = {"data": {"status": {
                "status": "healthy", "dlqSize": 0, "outboundDlqSize": 0,
                "queueDepth": 5, "activeWorkers": 4, "totalWorkers": 4,
                "uptime": 3600, "version": "v0.1.0-beta",
                "sourcesTotal": 3, "destinationsTotal": 2,
                "subscriptionsTotal": 5, "eventsTotal": 1000,
                "eventsFailed": 10, "deliveriesTotal": 900,
                "deliveriesPending": 50, "deliveriesDelivered": 840,
                "messagesTotal": 100,
                "outboundDeliveriesTotal": 80,
                "outboundDeliveriesPending": 5,
                "outboundDeliveriesFailed": 2,
            }}}
        elif "sources" in query and "mutation" not in query and "$id" not in query:
            resp = {"data": {"sources": {
                "nodes": [
                    {"id": "src-1", "name": "GitHub", "slug": "github",
                     "providerType": "github", "status": "ACTIVE",
                     "rateLimitRps": 100, "createdAt": "2025-01-01T00:00:00Z"},
                ],
                "pageInfo": {"total": 1, "limit": 20, "offset": 0,
                             "endCursor": None, "hasNextPage": False},
            }}}
        elif "source" in query and "$id" in query and "mutation" not in query:
            variables = body.get("variables", {})
            if variables.get("id") == "not-found":
                resp = {"errors": [{"message": "source not found", "extensions": {"code": "NOT_FOUND"}}]}
            else:
                resp = {"data": {"source": {
                    "id": "src-1", "name": "GitHub", "slug": "github",
                    "providerType": "github", "status": "ACTIVE",
                    "rateLimitRps": 100, "createdAt": "2025-01-01T00:00:00Z",
                }}}
        elif "createSource" in query:
            variables = body.get("variables", {})
            inp = variables.get("input", {})
            resp = {"data": {"createSource": {
                "id": "src-new", "name": inp.get("name", ""),
                "slug": inp.get("slug", ""),
                "providerType": inp.get("providerType", ""),
                "status": "ACTIVE", "rateLimitRps": 0,
                "createdAt": "2025-01-01T00:00:00Z",
            }}}
        elif "deleteSource" in query:
            resp = {"data": {"deleteSource": True}}
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


def test_list_sources(client):
    result = client.sources.list()
    assert len(result.nodes) == 1
    assert isinstance(result.nodes[0], Source)
    assert result.nodes[0].slug == "github"
    assert result.page_info.total == 1


def test_get_source(client):
    source = client.sources.get("src-1")
    assert source is not None
    assert source.id == "src-1"
    assert source.name == "GitHub"


def test_get_source_not_found(client):
    with pytest.raises(NotFoundError):
        client.sources.get("not-found")


def test_create_source(client):
    source = client.sources.create(
        name="Stripe", slug="stripe", provider_type="stripe",
    )
    assert source.id == "src-new"
    assert source.name == "Stripe"


def test_delete_source(client):
    result = client.sources.delete("src-1")
    assert result is True


def test_get_status(client):
    status = client.status.get()
    assert isinstance(status, SystemStatus)
    assert status.status == "healthy"
    assert status.version == "v0.1.0-beta"
    assert status.events_total == 1000
    assert status.active_workers == 4


def test_auth_error(server):
    bad_client = HivehookClient(api_key="bad_key", base_url=server)
    with pytest.raises(AuthError):
        bad_client.sources.list()


def test_client_default_base_url():
    c = HivehookClient(api_key="key")
    assert c.sources is not None


def test_list_sources_with_filters(client):
    result = client.sources.list(status="ACTIVE", limit=10)
    assert len(result.nodes) == 1


def test_page_info(client):
    result = client.sources.list()
    assert result.page_info.has_next_page is False
    assert result.page_info.limit == 20
