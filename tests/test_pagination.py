"""Zero-based paging and response conversion at the SDK/connector boundary."""

import pandas as pd
import pytest


PAGED_CASES = [
    ("getUsers", {}, "/configuration/orgs/users", "lastPage"),
    ("getTags", {}, "/componentmetadata/tags", "lastPage"),
    ("getSegments", {}, "/segments", "lastPage"),
    ("getCalculatedMetrics", {}, "/calculatedmetrics", "lastPage"),
    (
        "getDimensions",
        {"dataviewId": "dv-1"},
        "/data/dataviews/dv-1/dimensions",
        "lastPage",
    ),
    ("getMetrics", {"dataviewId": "dv-1"}, "/data/dataviews/dv-1/metrics", "lastPage"),
    ("getDataViews", {}, "/data/dataviews", "lastPage"),
    ("getConnections", {}, "/data/connections", "lastPage"),
    ("getProjects", {"limit": 1}, "/projects", "lastPage"),
]


@pytest.mark.parametrize(
    "method,arguments,path,last_key", PAGED_CASES, ids=[c[0] for c in PAGED_CASES]
)
def test_all_pages_are_loaded(client, queued_pages, method, arguments, path, last_key):
    calls = queued_pages(
        [
            {"content": [{"id": "first"}], last_key: False},
            {"content": [{"id": "second"}], last_key: True},
        ]
    )
    if method not in {"getUsers", "getTags"}:
        arguments = dict(arguments, output="raw")
    result = getattr(client, method)(**arguments)
    assert result == [{"id": "first"}, {"id": "second"}]
    assert [url for url, _ in calls] == ["https://cja.adobe.io" + path] * 2
    assert [kwargs["params"].get("page", 0) for _, kwargs in calls] == [0, 1]


@pytest.mark.parametrize(
    "method,arguments,path,last_key",
    [case for case in PAGED_CASES if case[0] not in {"getUsers", "getTags"}],
    ids=[c[0] for c in PAGED_CASES if c[0] not in {"getUsers", "getTags"}],
)
@pytest.mark.parametrize("empty", [False, True], ids=["rows", "empty"])
def test_dataframe_output(
    client, queued_pages, method, arguments, path, last_key, empty
):
    records = [] if empty else [{"id": "first", "name": "First"}]
    calls = queued_pages([{"content": records, last_key: True}])
    result = getattr(client, method)(**arguments)
    assert isinstance(result, pd.DataFrame)
    assert result.to_dict(orient="records") == records
    assert len(calls) == 1


@pytest.mark.parametrize("records", [[{"id": 1, "name": "Important"}], []])
def test_tags_load_paginated_response(client, queued_pages, records):
    """Use the service response confirmed in review ISSUE-09, not the OpenAPI array."""
    calls = queued_pages([{"content": records, "lastPage": True}])
    assert client.getTags() == records
    assert len(calls) == 1


def test_segments_forward_filters_and_can_disable_cache(client, queued_pages):
    queued_pages([{"content": [{"id": "seg-1"}], "lastPage": True}])
    result = client.getSegments(
        name="Loyal",
        dataIds="dv-1,dv-2",
        ownerId="owner-1",
        filterByIds="seg-1",
        cached=False,
        cache=False,
        output="raw",
        includeType="shared",
        limit=5,
    )
    assert result == [{"id": "seg-1"}]
    assert client.segments == []
    assert client.connector.getData.call_args.kwargs["params"] == {
        "page": 0,
        "limit": 5,
        "cached": False,
        "includeType": "shared",
        "name": "Loyal",
        "dataIds": "dv-1,dv-2",
        "ownerId": "owner-1",
        "filterByIds": "seg-1",
    }


def test_segments_cache_loaded_records(client, queued_pages):
    queued_pages([{"content": [{"id": "seg-1"}], "lastPage": True}])
    result = client.getSegments(output="raw")
    assert client.segments == result


def test_calculated_metric_cache_contains_all_pages(client, queued_pages):
    queued_pages(
        [
            {"content": [{"id": "cm-1"}], "lastPage": False},
            {"content": [{"id": "cm-2"}], "lastPage": True},
        ]
    )
    result = client.getCalculatedMetrics()
    pd.testing.assert_frame_equal(client.calculatedMetrics, result)
    assert result["id"].tolist() == ["cm-1", "cm-2"]


def test_audit_log_user_type_filter(client, queued_pages):
    queued_pages([{"content": [], "last": True}])
    client.getAuditLogs(userType="USER")
    assert client.connector.getData.call_args.kwargs["params"]["userType"] == "USER"


def test_audit_logs_raw_output(client, queued_pages):
    records = [{"action": "CREATE", "user": {"id": "user-1"}}]
    queued_pages([{"content": records, "last": True}])
    result = client.getAuditLogs(output="raw")
    assert isinstance(result, list)
    assert result == records


def test_audit_logs_dataframe_flattens_metadata(client, queued_pages):
    calls = queued_pages(
        [
            {
                "content": [
                    {
                        "action": "CREATE",
                        "user": {"id": "user-1"},
                        "component": {
                            "id": "project-1",
                            "idType": "PROJECT",
                            "name": "Project",
                        },
                    }
                ],
                "last": False,
            },
            {"content": [], "last": True},
        ]
    )
    result = client.getAuditLogs()
    assert result.loc[
        0, ["userId", "componentId", "componentType", "componentName"]
    ].tolist() == [
        "user-1",
        "project-1",
        "PROJECT",
        "Project",
    ]
    assert [kwargs["params"]["pageNumber"] for _, kwargs in calls] == [0, 1]


def test_data_views_follow_recorded_page_shape(client, queued_pages):
    """The data views endpoint sends lastPage and no last key.

    These page fields were recorded from a real org (content left out): 111
    data views across two pages of 100. Stopping on a missing ``last`` key
    returned only the first page.
    """
    calls = queued_pages(
        [
            {
                "content": [{"id": "dv-1"}],
                "firstPage": True,
                "lastPage": False,
                "number": 0,
                "numberOfElements": 100,
                "size": 100,
                "sort": None,
                "totalElements": 111,
                "totalPages": 2,
            },
            {
                "content": [{"id": "dv-2"}],
                "firstPage": False,
                "lastPage": True,
                "number": 1,
                "numberOfElements": 11,
                "size": 100,
                "sort": None,
                "totalElements": 111,
                "totalPages": 2,
            },
        ]
    )
    assert client.getDataViews(output="raw") == [{"id": "dv-1"}, {"id": "dv-2"}]
    assert [kwargs["params"]["page"] for _, kwargs in calls] == [0, 1]


def test_data_views_still_accept_a_last_key(client, queued_pages):
    queued_pages(
        [
            {"content": [{"id": "dv-1"}], "last": False},
            {"content": [{"id": "dv-2"}], "last": True},
        ]
    )
    assert client.getDataViews(output="raw") == [{"id": "dv-1"}, {"id": "dv-2"}]
