import importlib
import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("Tests must not make HTTP requests")

    monkeypatch.setattr(requests.sessions.Session, "request", blocked)


@pytest.fixture(scope="session")
def sdk():
    """Unblock method tests without hiding the independent import smoke failure."""
    package = Path(__file__).resolve().parents[1] / "cjapy"
    if (package / "version.py").exists():
        return importlib.import_module("cjapy")
    spec = importlib.util.spec_from_file_location(
        "cjapy.version", package / "__version__.py"
    )
    version = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(version)
    with pytest.MonkeyPatch.context() as patch:
        patch.setitem(sys.modules, "cjapy.version", version)
        return importlib.import_module("cjapy")


@pytest.fixture
def isolated_config(sdk):
    config = sdk.ConfigObj(
        org_id="test-org@AdobeOrg",
        client_id="test-client",
        secret="test-secret",
        scopes="openid,additional_info.projectedProductContext",
    )
    config.config_object.update(token="test-token", date_limit=float("inf"))
    config.header["Authorization"] = "Bearer test-token"
    return config


@pytest.fixture
def client(sdk, monkeypatch, isolated_config):
    transport = Mock(
        spec=[
            "getData",
            "postData",
            "putData",
            "patchData",
            "deleteData",
            "header",
            "config",
        ]
    )
    transport.header = deepcopy(isolated_config.header)
    transport.config = deepcopy(isolated_config.config_object)
    connector = importlib.import_module("cjapy.connector")
    monkeypatch.setattr(connector, "AdobeRequest", Mock(return_value=transport))
    return sdk.CJA(config_object=isolated_config)


@pytest.fixture
def queued_pages(client):
    def queue(responses):
        calls = []
        pages = iter(deepcopy(responses))

        def respond(url, **kwargs):
            calls.append((url, deepcopy(kwargs)))
            try:
                return next(pages)
            except StopIteration:
                pytest.fail("Pagination requested an unexpected extra page")

        client.connector.getData.side_effect = respond
        client.connector.postData.side_effect = respond
        return calls

    return queue


@pytest.fixture
def report_request(sdk):
    request = sdk.RequestCreator()
    request.setDataViewId("dv-test")
    request.setDimensions("variables/page")
    request.addMetric("metrics/pageviews")
    request.setDateRange("2025-01-01", "2025-01-31")
    return request.to_dict()
