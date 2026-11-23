"""Local transport fixtures; no Adobe credentials or external connections."""

import json
import socket
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace

import pytest
import urllib3.util.retry as retry_module

from cjapy.connector import AdobeRequest


@pytest.fixture(autouse=True)
def loopback_only(monkeypatch):
    """Fail before DNS or a connection can reach anything except our IPv4 server."""
    original_getaddrinfo = socket.getaddrinfo
    original_connect = socket.socket.connect

    def getaddrinfo(host, *args, **kwargs):
        assert host == "127.0.0.1", "Tests may only resolve the local HTTP server"
        return original_getaddrinfo(host, *args, **kwargs)

    def connect(sock, address):
        assert address[0] == "127.0.0.1", "Tests may only connect to loopback"
        return original_connect(sock, address)

    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", connect)


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
