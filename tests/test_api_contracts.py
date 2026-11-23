"""Request contracts from AdobeDocs/cja-apis static/swagger.json.

Reference: https://developer.adobe.com/cja-apis/docs/api
Expectations are independent of the SDK implementation. No live API is called.
"""

import json

import pytest


GET_CASES = [
    ("getCurrentUser", {}, "/configuration/users/me"),
    ("getShare", {"shareId": "share-1"}, "/componentmetadata/shares/share-1"),
    ("getShares", {}, "/componentmetadata/shares"),
    (
        "getAssetCount",
        {"imsUserId": "user-1"},
        "/componentmetadata/assets/user-1/counts",
    ),
    ("getTag", {"tagId": "tag-1"}, "/componentmetadata/tags/tag-1"),
    ("getDateRange", {"dateRangeId": "dr-1"}, "/dateranges/dr-1"),
    ("getCalculatedMetric", {"calcId": "cm-1"}, "/calculatedmetrics/cm-1"),
    ("getCalculatedMetricsFunctions", {}, "/calculatedmetrics/functions"),
    ("getDataView", {"dataViewId": "dv-1"}, "/data/dataviews/dv-1"),
    ("getConnection", {"connectionId": "conn-1"}, "/data/connections/conn-1"),
    ("getSegment", {"segmentId": "seg-1"}, "/segments/seg-1"),
    ("getProject", {"projectId": "project-1", "cache": False}, "/projects/project-1"),
    (
        "getDimension",
        {"dataviewId": "dv-1", "dimensionId": "dimension-1"},
        "/data/dataviews/dv-1/dimensions/dimension-1",
    ),
    (
        "getMetric",
        {"dataviewId": "dv-1", "metricId": "metric-1"},
        "/data/dataviews/dv-1/metrics/metric-1",
    ),
    (
        "getComponentTags",
        {"componentId": "seg-1", "componentType": "segment"},
        "/componentmetadata/tags/search",
    ),
    (
        "getTopItems",
        {"dataId": "dv-1", "dimension": "variables/page"},
        "/reports/topItems",
    ),
]


@pytest.mark.parametrize(
    "method,arguments,path", GET_CASES, ids=[c[0] for c in GET_CASES]
)
def test_get_routes_and_response_passthrough(client, method, arguments, path):
    response = {"id": "result", "additionalFutureField": "preserved"}
    client.connector.getData.return_value = response
    assert getattr(client, method)(**arguments) == response
    client.connector.getData.assert_called_once()
    assert client.connector.getData.call_args.args == ("https://cja.adobe.io" + path,)
    assert len(client.connector.mock_calls) == 1


DELETE_CASES = [
    ("deleteShare", {"shareId": "share-1"}, "/componentmetadata/shares/share-1"),
    ("deleteDateRange", {"dateRangeId": "dr-1"}, "/dateranges/dr-1"),
    ("deleteCalculateMetrics", {"calcId": "cm-1"}, "/calculatedmetrics/cm-1"),
    ("deleteDataView", {"dataViewId": "dv-1"}, "/data/dataviews/dv-1"),
    ("deleteSegment", {"segmentId": "seg-1"}, "/segments/seg-1"),
    ("deleteProject", {"projectId": "project-1"}, "/projects/project-1"),
]


@pytest.mark.parametrize(
    "method,arguments,path", DELETE_CASES, ids=[c[0] for c in DELETE_CASES]
)
def test_delete_routes(client, method, arguments, path):
    client.connector.deleteData.return_value = 204
    assert getattr(client, method)(**arguments) == 204
    client.connector.deleteData.assert_called_once_with("https://cja.adobe.io" + path)


BODY_CASES = [
    (
        "validateCalculatedMetric",
        {},
        "data",
        {},
        "postData",
        "/calculatedmetrics/validate",
    ),
    (
        "searchShares",
        {},
        "data",
        {},
        "postData",
        "/componentmetadata/shares/component/search",
    ),
    ("updateShares", {}, "data", [], "putData", "/componentmetadata/shares"),
    ("createDateRange", {}, "dateRangeData", {}, "postData", "/dateranges"),
    (
        "updateDateRange",
        {"dateRangeId": "dr-1"},
        "data",
        {},
        "putData",
        "/dateranges/dr-1",
    ),
    ("createTags", {}, "data", [], "postData", "/componentmetadata/tags"),
    ("updateTags", {}, "data", [], "putData", "/componentmetadata/tags/tagitems"),
    ("validateDataView", {}, "data", {}, "postData", "/data/dataviews/validate"),
    ("createDataView", {}, "data", {}, "postData", "/data/dataviews"),
    (
        "updateDataView",
        {"dataViewId": "dv-1"},
        "data",
        {},
        "putData",
        "/data/dataviews/dv-1",
    ),
    ("createSegment", {}, "data", {}, "postData", "/segments"),
    ("validateSegment", {}, "data", {}, "postData", "/segments/validate"),
    ("updateSegment", {"segmentId": "seg-1"}, "data", {}, "putData", "/segments/seg-1"),
    (
        "updateCalculatedMetrics",
        {"calcId": "cm-1"},
        "data",
        {},
        "putData",
        "/calculatedmetrics/cm-1",
    ),
    (
        "transferAssets",
        {"imsUserId": "user-1"},
        "assets",
        [],
        "putData",
        "/componentmetadata/assets/user-1/transfer",
    ),
    (
        "searchAuditLogs",
        {},
        "filterMessage",
        {},
        "postData",
        "/auditlogs/api/v1/auditlogs/search",
    ),
    ("createProject", {}, "projectDefinition", {}, "postData", "/projects"),
    ("validateProject", {}, "projectDefinition", {}, "postData", "/projects/validate"),
    (
        "updateProject",
        {"projectId": "p-1"},
        "projectDefinition",
        {},
        "putData",
        "/projects/p-1",
    ),
]


@pytest.mark.parametrize(
    "method,arguments,body_argument,body,verb,path",
    BODY_CASES,
    ids=[c[0] for c in BODY_CASES],
)
def test_write_routes_and_payloads(
    client, method, arguments, body_argument, body, verb, path
):
    payload = [{"id": "component-1"}] if isinstance(body, list) else {"name": "Test"}
    response = {"id": "created", "name": "Test"}
    getattr(client.connector, verb).return_value = response
    result = getattr(client, method)(**arguments, **{body_argument: payload})
    transport = getattr(client.connector, verb)
    transport.assert_called_once()
    assert result == response
    assert transport.call_args.args[0].rstrip("/") == "https://cja.adobe.io" + path
    expected_body = {"project": payload} if method == "validateProject" else payload
    assert transport.call_args.kwargs["data"] == expected_body
    assert len(client.connector.mock_calls) == 1


@pytest.mark.parametrize(
    "method",
    [case[0] for case in DELETE_CASES]
    + [
        "getShare",
        "getAssetCount",
        "getTag",
        "getDateRange",
        "getCalculatedMetric",
        "getDataView",
        "getConnection",
        "getSegment",
        "getProject",
        "getDimensions",
        "getDimension",
        "getMetrics",
        "getMetric",
        "getTopItems",
        "getComponentTags",
        "createDateRange",
        "createTags",
        "updateTags",
        "updateShares",
        "searchShares",
        "createSegment",
        "updateSegment",
        "validateSegment",
        "validateCalculatedMetric",
        "updateCalculatedMetrics",
        "createProject",
        "updateProject",
        "validateProject",
        "searchAuditLogs",
        "createDataView",
        "updateDataView",
        "copyDataView",
    ],
)
def test_missing_required_arguments_never_send_requests(client, method):
    with pytest.raises(ValueError):
        getattr(client, method)()
    assert client.connector.mock_calls == []


def test_delete_tags_uses_documented_query_names(client):
    client.connector.deleteData.return_value = 204
    client.deleteTags(componentIds="seg-1,seg-2", componentType="segment")
    client.connector.deleteData.assert_called_once_with(
        "https://cja.adobe.io/componentmetadata/tags",
        params={"componentIds": "seg-1,seg-2", "componentType": "segment"},
    )


def test_current_user_admin_expansion(client):
    client.getCurrentUser(admin=True, useCache=False)
    assert client.connector.getData.call_args.kwargs["params"] == {
        "useCache": False,
        "expansion": "admin",
    }


def test_top_items_optional_query_parameters(client):
    client.getTopItems(
        dataId="dv-1",
        dimension="variables/page",
        limit=3,
        dateRange="2025-01-01/2025-02-01",
        searchClause="CONTAINS 'home'",
        remoteLoad=False,
        xml=True,
        noneValues=False,
    )
    assert client.connector.getData.call_args.kwargs["params"] == {
        "dataId": "dv-1",
        "dimension": "variables/page",
        "limit": 3,
        "dateRange": "2025-01-01/2025-02-01",
        "search-clause": "CONTAINS 'home'",
        "allowRemoteLoad": "false",
        "includeOberonXml": True,
        "lookupNoneValues": False,
    }


@pytest.mark.parametrize(
    "method,arguments,verb",
    [
        ("createSegment", {}, "postData"),
        ("validateSegment", {}, "postData"),
        ("updateSegment", {"segmentId": "seg-1"}, "putData"),
        ("validateDataView", {}, "postData"),
        ("createDataView", {}, "postData"),
        ("updateDataView", {"dataViewId": "dv-1"}, "putData"),
    ],
)
def test_json_definition_files_are_loaded(client, tmp_path, method, arguments, verb):
    payload = {"name": "Loaded from file", "definition": {"func": "segment"}}
    path = tmp_path / "definition.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    getattr(client, method)(data=str(path), **arguments)
    assert getattr(client.connector, verb).call_args.kwargs["data"] == payload


@pytest.mark.parametrize("payload", [{}, "not-a-list", 42])
def test_create_tags_rejects_non_list_payloads(client, payload):
    with pytest.raises(ValueError):
        client.createTags(data=payload)
    assert client.connector.mock_calls == []


def test_copy_dataview_uses_put(client):
    client.copyDataView("dv-1")
    client.connector.putData.assert_called_once_with(
        "https://cja.adobe.io/data/dataviews/copy/dv-1"
    )
