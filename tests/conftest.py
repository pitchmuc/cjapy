"""Offline SDK and local transport fixtures; no Adobe credentials."""

import json
import socket
from collections import deque
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from types import ModuleType, SimpleNamespace
from typing import Any, Callable, Iterator
from unittest.mock import create_autospec

import cjapy
import pytest
import urllib3.util.retry as retry_module

from cjapy import config, configs
from cjapy.connector import AdobeRequest


Page = dict[str, Any]
RequestCalls = list[tuple[str, dict[str, Any]]]


@pytest.fixture
def sdk(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    isolated_globals = {
        "config_object": deepcopy(config.config_object),
        "header": deepcopy(config.header),
    }
    # These modules import the same mutable dictionaries by reference.
    for module in (config, configs, cjapy):
        for name, value in isolated_globals.items():
            monkeypatch.setattr(module, name, value)
    return cjapy


@pytest.fixture
def isolated_config(sdk: ModuleType) -> cjapy.ConfigObj:
    credentials = sdk.ConfigObj(org_id="test-org", client_id="test-client")
    credentials.config_object.update(token="test-token", date_limit=float("inf"))
    credentials.header["Authorization"] = "Bearer test-token"
    return credentials


@pytest.fixture
def client(sdk: ModuleType, isolated_config: cjapy.ConfigObj) -> Iterator[cjapy.CJA]:
    instance = sdk.CJA(config_object=isolated_config)
    transport = instance.connector
    try:
        instance.connector = create_autospec(transport, spec_set=True)
        yield instance
    finally:
        transport.session.close()


@pytest.fixture
def queued_pages(client: cjapy.CJA) -> Callable[[list[Page]], RequestCalls]:
    def queue(pages: list[Page]) -> RequestCalls:
        responses = iter(deepcopy(pages))
        calls: RequestCalls = []

        def respond(url: str, **kwargs: Any) -> Page:
            calls.append((url, deepcopy(kwargs)))
            try:
                return next(responses)
            except StopIteration:
                pytest.fail("Unexpected extra pagination request")

        client.connector.getData.side_effect = respond
        client.connector.postData.side_effect = respond
        return calls

    return queue


@pytest.fixture
def report_request() -> Page:
    return {
        "dataId": "dv-1",
        "dimensions": [{"columnId": "col0", "id": "variables/page"}],
        "metricContainer": {
            "metrics": [{"columnId": "0", "id": "metrics/pageviews"}],
            "metricFilters": [],
        },
        "globalFilters": [
            {
                "type": "dateRange",
                "dateRange": "2025-01-01T00:00:00.000/2025-01-31T23:59:59.999",
            }
        ],
        "settings": {"countRepeatInstances": True, "page": 0, "limit": 20000},
        "statistics": {"functions": ["col-max", "col-min"]},
    }


@pytest.fixture(autouse=True)
def loopback_only(monkeypatch):
    """Fail before DNS or a connection can reach anything except our IPv4 server."""
    original_getaddrinfo = socket.getaddrinfo
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def getaddrinfo(host, *args, **kwargs):
        assert host == "127.0.0.1", "Tests may only resolve the local HTTP server"
        return original_getaddrinfo(host, *args, **kwargs)

    def connect(sock, address):
        assert address[0] == "127.0.0.1", "Tests may only connect to loopback"
        return original_connect(sock, address)

    def connect_ex(sock, address):
        assert address[0] == "127.0.0.1", "Tests may only connect to loopback"
        return original_connect_ex(sock, address)

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)


@pytest.fixture
def retry_clock(monkeypatch):
    """Keep Retry's calculations real; record waits without wall-clock delays."""
    sleeps = []
    monkeypatch.setattr(
        retry_module, "time", SimpleNamespace(time=lambda: 1700000000, sleep=sleeps.append)
    )
    return sleeps


@pytest.fixture
def connector_factory():
    connectors = []

    def create(**kwargs):
        connector = AdobeRequest(
            config_object={
                "org_id": "test-org",
                "token": "not-a-real-token",
                "date_limit": float("inf"),
            },
            header={"Authorization": "Bearer not-a-real-token"},
            **kwargs,
        )
        # Ignore the contributor's proxies and .netrc credentials.
        connector.session.trust_env = False
        connectors.append(connector)
        return connector

    yield create
    for connector in connectors:
        connector.session.close()


@pytest.fixture
def http_server():
    """Serve scripted responses through real sockets, repeating the final response."""
    responses = deque()
    received = []

    class Handler(BaseHTTPRequestHandler):
        def respond(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            received.append({"method": self.command, "path": self.path, "body": body})
            status, payload, headers = responses[0]
            if len(responses) > 1:
                responses.popleft()
            content = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            for name, value in headers.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(content)

        do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = respond

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()

    def script(*items):
        responses.extend(items)
        return "http://127.0.0.1:{}/resource".format(server.server_port), received

    try:
        yield script
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        assert not thread.is_alive()
