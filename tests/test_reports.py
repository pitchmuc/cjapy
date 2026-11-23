from copy import deepcopy
import json

import pandas as pd
import pytest


def report_page(item_id, value, count, last):
    return {
        "rows": [{"itemId": item_id, "value": value, "data": [count]}],
        "columns": {"columnIds": ["0"], "dimension": {"id": "variables/page"}},
        "summaryData": {"totals": [30]},
        "numberOfElements": 1,
        "lastPage": last,
        "resultsTruncated": False,
    }


def test_report_loads_all_pages_without_mutating_input(
    client, queued_pages, report_request
):
    original = deepcopy(report_request)
    calls = queued_pages(
        [
            report_page("1", "Home", 10, False),
            report_page("2", "Checkout", 20, True),
        ]
    )
    result = client.getReport(report_request, limit=1, returnClass=False)
    assert result == [
        {"itemId": "1", "value": "Home", "data": [10]},
        {"itemId": "2", "value": "Checkout", "data": [20]},
    ]
    assert report_request == original
    assert [url for url, _ in calls] == ["https://cja.adobe.io/reports"] * 2
    assert [kwargs["data"]["settings"]["page"] for _, kwargs in calls] == [0, 1]


@pytest.mark.parametrize("source", ["dictionary", "builder", "json"])
def test_report_input_formats(
    client, sdk, queued_pages, report_request, tmp_path, source
):
    queued_pages([report_page("1", "Home", 10, True)])
    if source == "builder":
        request = sdk.RequestCreator(report_request)
    elif source == "json":
        path = tmp_path / "report.json"
        path.write_text(json.dumps(report_request), encoding="utf-8")
        request = str(path)
    else:
        request = report_request
    result = client.getReport(request, returnClass=False)
    assert result == [{"itemId": "1", "value": "Home", "data": [10]}]


def test_workspace_loads_response_metadata(client, sdk, queued_pages, report_request):
    queued_pages([report_page("1", "Home", 10, True)])
    workspace = client.getReport(report_request, resolveColumns=False)
    assert isinstance(workspace, sdk.Workspace)
    assert workspace.dataframe.to_dict(orient="records") == [
        {
            "itemId": "1",
            "variables/page": "Home",
            "metrics/pageviews": 10,
        }
    ]
    assert workspace.summaryData == {"totals": [30]}
    assert workspace.startDate == "2025-01-01T00:00:00.000"
    assert workspace.endDate == "2025-01-31T23:59:59.999"
    assert workspace.row_numbers == 1
    assert workspace.pageRequested == 1
    assert workspace.resultsTruncated is False


def test_report_stops_fetching_at_result_limit(client, queued_pages, report_request):
    calls = queued_pages([report_page("1", "Home", 10, False)])
    result = client.getReport(report_request, n_results=1, returnClass=False)
    assert len(result) == 1
    assert len(calls) == 1


def test_empty_report_returns_empty_workspace(client, queued_pages, report_request):
    page = report_page("1", "Home", 10, True)
    page.update(rows=[], numberOfElements=0)
    queued_pages([page])
    assert client.getReport(report_request, resolveColumns=False).dataframe.empty


@pytest.mark.parametrize("return_class", [True, False])
def test_report_timeout_raises(client, report_request, return_class):
    client.connector.postData.return_value = {"error-504": "504 Gateway Time-out"}
    with pytest.raises(TimeoutError, match="504"):
        client.getReport(report_request, returnClass=return_class)


@pytest.mark.parametrize("return_nones", [True, False])
@pytest.mark.parametrize("dimension_count", [1, 2])
def test_report_explicit_none_behavior(
    client, queued_pages, report_request, return_nones, dimension_count
):
    if dimension_count == 2:
        report_request["dimensions"].append(
            {"columnId": "col1", "id": "variables/product"}
        )
    calls = queued_pages([report_page("1", "Home", 10, True)])
    client.getReport(report_request, returnsNone=return_nones, returnClass=False)
    expected = (
        "return-nones" if return_nones or dimension_count == 2 else "exclude-nones"
    )
    assert calls[0][1]["data"]["settings"]["nonesBehavior"] == expected


@pytest.mark.parametrize("request_setting", [True, False, None])
def test_report_preserves_repeat_instance_setting_when_not_overridden(
    client, queued_pages, report_request, request_setting
):
    calls = queued_pages([report_page("1", "Home", 10, True)])
    if request_setting is None:
        del report_request["settings"]["countRepeatInstances"]
    else:
        report_request["settings"]["countRepeatInstances"] = request_setting
    original = deepcopy(report_request)
    client.getReport(report_request, returnClass=False)
    expected = False if request_setting is None else request_setting
    assert calls[0][1]["data"]["settings"]["countRepeatInstances"] is expected
    assert report_request == original


@pytest.mark.parametrize("override", [True, False])
def test_report_repeat_instance_override(
    client, queued_pages, report_request, override
):
    calls = queued_pages([report_page("1", "Home", 10, True)])
    report_request["settings"]["countRepeatInstances"] = not override
    original = deepcopy(report_request)
    client.getReport(report_request, countRepeatInstances=override, returnClass=False)
    assert calls[0][1]["data"]["settings"]["countRepeatInstances"] is override
    assert report_request == original


@pytest.mark.parametrize("format", ["csv", "json"])
def test_workspace_exports_loaded_dataframe(
    client, queued_pages, report_request, tmp_path, format
):
    queued_pages([report_page("1", "Home", 10, True)])
    workspace = client.getReport(report_request, resolveColumns=False)
    path = tmp_path / ("report." + format)
    if format == "csv":
        workspace.to_csv(str(path))
        loaded = pd.read_csv(path, dtype={"itemId": str})
    else:
        workspace.to_json(str(path))
        loaded = pd.read_json(path, orient="index", dtype={"itemId": str})
    assert loaded.to_dict(orient="records") == workspace.dataframe.to_dict(
        orient="records"
    )
