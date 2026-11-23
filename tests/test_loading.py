import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_clean_process_imports_without_credentials(tmp_path):
    root = Path(__file__).resolve().parents[1]
    script = """
import importlib
import socket

def blocked(*args, **kwargs):
    raise AssertionError("Package imports must not access the network")

socket.socket.connect = blocked
import cjapy
for name in ("config", "configs", "connector", "cjapy", "projects",
             "requestCreator", "workspace", "__version__"):
    importlib.import_module("cjapy." + name)
for name in ("CJA", "ConfigObj", "configure", "importConfigFile",
             "RequestCreator", "Workspace", "Project"):
    assert callable(getattr(cjapy, name)), name
assert isinstance(cjapy.__version__, str)
assert cjapy.__version__
assert cjapy.config_object["org_id"] == ""
assert cjapy.config_object["token"] == ""
"""
    environment = dict(os.environ, PYTHONPATH=str(root))
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_config_objects_do_not_share_credentials(sdk):
    first = sdk.ConfigObj(org_id="first", client_id="first-client")
    second = sdk.ConfigObj(org_id="second", client_id="second-client")
    first.config_object["token"] = "first-token"
    first.header["Authorization"] = "Bearer first-token"
    assert second.config_object["token"] == ""
    assert second.header["Authorization"] == "Bearer "
    assert second.header["x-api-key"] == "second-client"


@pytest.mark.parametrize("missing", ["org_id", "client_id", "secret", "scopes"])
def test_configure_requires_credentials(sdk, missing):
    arguments = dict(org_id="org", client_id="client", secret="secret", scopes="scope")
    arguments.pop(missing)
    with pytest.raises(ValueError, match=missing):
        sdk.configure(**arguments)


@pytest.mark.parametrize(
    "credentials",
    [
        {"org_id": "org", "client_id": "client", "secret": "secret", "scopes": "a, b"},
        {
            "org_id": "org",
            "api_key": "client",
            "secret": "secret",
            "scopes": ["a", "b"],
        },
        {
            "ORG_ID": "org",
            "CLIENT_ID": "client",
            "CLIENT_SECRETS": ["unused", "secret"],
            "SCOPES": ["a", "b"],
        },
    ],
)
def test_load_configuration_formats_without_changing_globals(
    sdk, tmp_path, credentials
):
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps(credentials), encoding="utf-8")
    original_config = sdk.config_object.copy()
    original_headers = sdk.header.copy()
    result = sdk.importConfigFile(
        str(path),
        return_object=True,
        client_secret_index=1 if "CLIENT_SECRETS" in credentials else 0,
    )
    assert isinstance(result, sdk.ConfigObj)
    assert result.config_object["org_id"] == "org"
    assert result.config_object["client_id"] == "client"
    assert result.config_object["secret"] == "secret"
    assert result.config_object["scopes"] == "a,b"
    assert sdk.config_object == original_config
    assert sdk.header == original_headers


def test_missing_configuration_file(sdk, tmp_path):
    with pytest.raises(FileNotFoundError):
        sdk.importConfigFile(str(tmp_path / "missing.json"))


def test_invalid_configuration_reports_missing_client(sdk, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="client_id"):
        sdk.importConfigFile(str(path))


def test_configuration_template_can_be_loaded(sdk, tmp_path):
    path = tmp_path / "template.json"
    sdk.createConfigFile(str(path))
    result = sdk.importConfigFile(str(path), return_object=True)
    assert isinstance(result, sdk.ConfigObj)
    assert result.config_object["token"] == ""


def test_client_constructor_uses_isolated_credentials(sdk, isolated_config):
    module = importlib.import_module("cjapy.connector")
    first = sdk.CJA(config_object=isolated_config)
    second_config = sdk.ConfigObj(org_id="other-org", client_id="other-client")
    second_config.config_object.update(token="other-token", date_limit=float("inf"))
    second_config.header["Authorization"] = "Bearer other-token"
    second = sdk.CJA(config_object=second_config)
    try:
        assert isinstance(first.connector, module.AdobeRequest)
        assert first.header["x-api-key"] == "test-client"
        assert second.header["x-api-key"] == "other-client"
        first.header["Authorization"] = "changed"
        assert isolated_config.header["Authorization"] == "Bearer test-token"
        assert second.header["Authorization"] == "Bearer other-token"
        assert first.endpoint == "https://cja.adobe.io"
    finally:
        first.connector.session.close()
        second.connector.session.close()


@pytest.mark.parametrize("suffix", [False, True])
def test_project_response_loads_nested_components(client, sdk, suffix):
    response = {
        "id": "project-1",
        "name": "Test project",
        "type": "project",
        "owner": {"name": "Test owner", "imsUserId": "owner-1", "login": "test-owner"},
        "definition": {
            "version": "1",
            "workspaces": [
                {
                    "id": "workspace-1",
                    "panels": [
                        {
                            "id": "panel-1",
                            "reportSuite": {
                                "id": "dv-1",
                                "__metaData__": {"name": "Test view"},
                            },
                            "subPanels": [
                                {
                                    "reportlet": {
                                        "type": "FreeformReportlet",
                                        "freeformTable": {
                                            "dimension": {"id": "variables/page"},
                                            "staticRows": [],
                                        },
                                        "columnTree": {
                                            "nodes": [
                                                {
                                                    "component": {
                                                        "type": "Segment",
                                                        "id": "segment-1",
                                                    },
                                                    "nodes": [
                                                        {
                                                            "component": {
                                                                "type": "Metric",
                                                                "id": "metrics/pageviews",
                                                            },
                                                            "nodes": [],
                                                        }
                                                    ],
                                                }
                                            ]
                                        },
                                    },
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    }
    client.connector.getData.return_value = response
    project = client.getProject("project-1", projectClass=True, dvIdSuffix=suffix)
    assert isinstance(project, sdk.Project)
    result = project.to_dict()
    ending = "::dv-1" if suffix else ""
    assert result["dimensions"] == ["variables/page" + ending]
    assert result["metrics"] == ["metrics/pageviews" + ending]
    assert result["filters"] == ["segment-1"]
    assert result["dataViewIds"] == ["dv-1"]
    assert result["nbPanels"] == 1
    assert result["nbSubPanels"] == 1
    assert result["nbElementsUsed"] == 3
