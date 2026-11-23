<<<<<<< HEAD
import importlib
import json
from unittest.mock import Mock
=======
"""Characterize AdobeRequest through its real requests/urllib3 retry adapter."""

import json
from email.utils import formatdate
>>>>>>> a1dfad406231ef805e839a5c2ba55481a93f6e41

import pytest


<<<<<<< HEAD
@pytest.fixture
def transport(sdk, isolated_config):
    module = importlib.import_module("cjapy.connector")
    connector = module.AdobeRequest(
        config_object=isolated_config.config_object,
        header=isolated_config.header,
    )
    original_session = connector.session
    connector.session = Mock()
    connector.session.headers = dict(connector.header)
    yield connector
    original_session.close()


@pytest.mark.parametrize("verb", ["post", "put", "patch"])
@pytest.mark.parametrize("with_params", [False, True])
@pytest.mark.parametrize("with_body", [False, True])
def test_write_serialization(transport, verb, with_params, with_body):
    response = {"id": "result", "futureField": True}
    getattr(transport.session, verb).return_value.json.return_value = response
    arguments = {"headers": {"X-Test": "test"}}
    if with_params:
        arguments["params"] = {"page": 1}
    if with_body:
        arguments["data"] = {"name": "Test", "enabled": True}
    result = getattr(transport, verb + "Data")(
        "https://cja.adobe.io/resource", **arguments
    )
    assert result == response
    expected = dict(arguments)
    if with_body:
        expected["data"] = json.dumps(arguments["data"])
    getattr(transport.session, verb).assert_called_once_with(
        "https://cja.adobe.io/resource", **expected
    )


def test_get_query_and_headers_are_forwarded(transport):
    transport.session.get.return_value.json.return_value = {"id": "result"}
    result = transport.getData(
        "https://cja.adobe.io/resource",
        params={"page": 0},
        expansion="definition",
        headers={"X-Test": "test"},
    )
    assert result == {"id": "result"}
    transport.session.get.assert_called_once_with(
        "https://cja.adobe.io/resource",
        params={"page": 0, "expansion": "definition"},
        data=None,
        headers={"X-Test": "test"},
    )


def test_delete_returns_http_status(transport):
    transport.session.delete.return_value.status_code = 204
    assert (
        transport.deleteData("https://cja.adobe.io/resource", params={"id": "one"})
        == 204
    )
    transport.session.delete.assert_called_once_with(
        "https://cja.adobe.io/resource",
        params={"id": "one"},
        headers=None,
    )


def test_oauth_client_credentials_payload(sdk, monkeypatch, isolated_config):
    module = importlib.import_module("cjapy.connector")
    post = Mock()
    post.return_value.json.return_value = {
        "access_token": "new-test-token",
        "expires_in": 86400,
    }
    monkeypatch.setattr(module.requests, "post", post)
    config = isolated_config.config_object.copy()
    config.update(token="", date_limit=0)
    connector = module.AdobeRequest(config_object=config, header=isolated_config.header)
    try:
        post.assert_called_once_with(
            "https://ims-na1.adobelogin.com/ims/token/v3",
            data={
                "grant_type": "client_credentials",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "scope": "openid,additional_info.projectedProductContext",
            },
        )
        assert connector.header["Authorization"] == "Bearer new-test-token"
        assert connector.session.headers["Authorization"] == "Bearer new-test-token"
        assert config["token"] == ""
    finally:
        connector.session.close()


@pytest.mark.parametrize(
    "response", [{"access_token": "token"}, {"expires_in": 3600}, {}]
)
def test_incomplete_oauth_response_raises(transport, monkeypatch, response):
    module = importlib.import_module("cjapy.connector")
    post = Mock()
    post.return_value.json.return_value = response
    monkeypatch.setattr(module.requests, "post", post)
    with pytest.raises(Exception, match="OAuth response missing required fields"):
        transport.get_oauth_token_and_expiry_for_config(transport.config)


def test_expired_token_refresh_updates_request_headers(transport, monkeypatch):
    module = importlib.import_module("cjapy.connector")
    monkeypatch.setattr(module.time, "time", lambda: 1000)
    transport.config["date_limit"] = 999
    transport.get_oauth_token_and_expiry_for_config = Mock(
        return_value={"token": "refreshed-token", "expiry": 3600}
    )
    transport.getData("https://cja.adobe.io/resource")
    assert transport.config["token"] == "refreshed-token"
    assert transport.config["date_limit"] == 4100
    assert transport.header["Authorization"] == "Bearer refreshed-token"
    assert transport.session.headers["Authorization"] == "Bearer refreshed-token"
    transport.get_oauth_token_and_expiry_for_config.assert_called_once()


def test_valid_token_is_not_refreshed(transport):
    transport.get_oauth_token_and_expiry_for_config = Mock()
    transport.getData("https://cja.adobe.io/resource")
    transport.get_oauth_token_and_expiry_for_config.assert_not_called()


@pytest.mark.parametrize("verb", ["get", "post", "put", "patch"])
def test_non_json_error_is_not_reported_as_success(transport, verb):
    response = getattr(transport.session, verb).return_value
    response.json.side_effect = ValueError("Not JSON")
    response.status_code = 500
    result = getattr(transport, verb + "Data")("https://cja.adobe.io/resource")
    assert "error" in result


def test_gateway_timeout_response(transport):
    response = transport.session.post.return_value
    response.json.side_effect = ValueError("Not JSON")
    response.status_code = 504
    assert transport.postData("https://cja.adobe.io/reports") == {
        "error-504": "504 Gateway Time-out",
    }
=======
METHODS = ["getData", "postData", "patchData", "putData", "deleteData"]
RETRYABLE_STATUSES = [429, 500, 502, 503, 504]


def call(connector, method, url):
    kwargs = {} if method in ("getData", "deleteData") else {"data": {"name": "test"}}
    return getattr(connector, method)(url, **kwargs)


@pytest.mark.parametrize("method", METHODS)
def test_successful_response(connector_factory, http_server, retry_clock, method):
    payload = {"items": [{"id": "123"}], "ok": True}
    url, received = http_server((200, payload, {}))

    result = call(connector_factory(), method, url)

    assert result == (200 if method == "deleteData" else payload)
    assert len(received) == 1
    assert received[0]["method"] == method.removesuffix("Data").upper()
    if method in ("postData", "patchData", "putData"):
        assert json.loads(received[0]["body"]) == {"name": "test"}
    assert retry_clock == []


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("status", RETRYABLE_STATUSES)
def test_transient_errors_retry_through_adapter(
    connector_factory, http_server, retry_clock, method, status
):
    payload = {"recovered": True}
    url, received = http_server(
        (status, {"error": "temporary"}, {}),
        (status, {"error": "temporary"}, {}),
        (200, payload, {}),
    )

    result = call(connector_factory(), method, url)

    assert result == (200 if method == "deleteData" else payload)
    assert len(received) == 3
    assert received == [received[0]] * 3  # The same method, path and body are replayed.
    assert retry_clock == [2.0]  # First retry is immediate, then exponential backoff.


@pytest.mark.parametrize("status", [429, 503])
@pytest.mark.parametrize("retry_after", ["7", formatdate(1700000007, usegmt=True)])
def test_retry_after_takes_precedence_over_backoff(
    connector_factory, http_server, retry_clock, status, retry_after
):
    url, received = http_server(
        (status, {}, {}),
        (status, {}, {"Retry-After": retry_after}),
        (200, {"recovered": True}, {}),
    )

    assert connector_factory().getData(url) == {"recovered": True}
    assert len(received) == 3
    assert retry_clock == [7]  # Would be 2 seconds if the header were ignored.


@pytest.mark.parametrize("retry_after", ["0", formatdate(1699999999, usegmt=True)])
def test_retry_after_zero_or_past_date_falls_back_to_backoff(
    connector_factory, http_server, retry_clock, retry_after
):
    url, received = http_server(
        (503, {}, {}),
        (503, {}, {"Retry-After": retry_after}),
        (200, {"recovered": True}, {}),
    )

    assert connector_factory().getData(url) == {"recovered": True}
    assert len(received) == 3
    assert retry_clock == [2.0]


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("status", RETRYABLE_STATUSES)
def test_retry_exhaustion_returns_final_response(
    connector_factory, http_server, retry_clock, method, status
):
    final_error = {"error": "still unavailable"}
    url, received = http_server(
        (status, {"error": "first attempt"}, {}),
        (status, final_error, {}),
    )

    # retry=0 still means three retries; raise_on_status=False returns the last response.
    result = call(connector_factory(retry=0), method, url)

    assert result == (status if method == "deleteData" else final_error)
    assert len(received) == 4
    assert retry_clock == [2.0, 4.0]


@pytest.mark.parametrize("retry, attempts, sleeps", [(1, 4, [2.0, 4.0]), (4, 5, [2.0, 4.0, 8.0])])
def test_retry_budget_has_a_floor_of_three(
    connector_factory, http_server, retry_clock, retry, attempts, sleeps
):
    url, received = http_server((503, {"error": "unavailable"}, {}))

    assert connector_factory(retry=retry).getData(url) == {"error": "unavailable"}
    assert len(received) == attempts
    assert retry_clock == sleeps


@pytest.mark.parametrize("method", METHODS)
def test_non_retryable_status_returns_immediately(
    connector_factory, http_server, retry_clock, method
):
    payload = {"error": "bad request"}
    url, received = http_server((400, payload, {}))

    assert call(connector_factory(), method, url) == (400 if method == "deleteData" else payload)
    assert len(received) == 1
    assert retry_clock == []
>>>>>>> a1dfad406231ef805e839a5c2ba55481a93f6e41
