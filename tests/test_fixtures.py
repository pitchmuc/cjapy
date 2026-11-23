from copy import deepcopy
import socket

import pytest


@pytest.mark.parametrize("method", ["getData", "postData"])
def test_queued_pages_preserves_requests_and_scripted_responses(
    client, queued_pages, method
):
    pages = [{"content": [{"id": "first"}], "lastPage": True}]
    original = deepcopy(pages)
    calls = queued_pages(pages)
    params = {"page": 0}
    data = {"settings": {"page": 0}}
    url = "https://cja.adobe.io/reports"

    response = getattr(client.connector, method)(url, params=params, data=data)
    params["page"] = 1
    data["settings"]["page"] = 1
    response["content"][0]["id"] = "changed"

    assert calls == [(url, {"params": {"page": 0}, "data": {"settings": {"page": 0}}})]
    assert pages == original


@pytest.mark.parametrize("method", ["getData", "postData"])
def test_queued_pages_fails_on_unexpected_extra_requests(client, queued_pages, method):
    queued_pages([{"content": [], "lastPage": True}])
    transport = getattr(client.connector, method)
    transport("https://cja.adobe.io/reports")

    with pytest.raises(pytest.fail.Exception, match="Unexpected extra pagination request"):
        transport("https://cja.adobe.io/reports")


def test_loopback_guard_blocks_external_resolution():
    with pytest.raises(AssertionError, match="Tests may only resolve the local HTTP server"):
        socket.getaddrinfo("192.0.2.1", 443, flags=socket.AI_NUMERICHOST)


@pytest.mark.parametrize("method", ["connect", "connect_ex"])
def test_loopback_guard_blocks_external_connections(method):
    # A broken guard must not let this regression test open an external connection.
    connection = socket.socket()
    connection.close()
    with pytest.raises(AssertionError, match="Tests may only connect to loopback"):
        getattr(connection, method)(("192.0.2.1", 443))
