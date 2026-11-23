import importlib
import json
from unittest.mock import Mock

import pytest


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
