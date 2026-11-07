"""Characterize AdobeRequest through its real requests/urllib3 retry adapter."""

import json
from email.utils import formatdate

import pytest


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
