from copy import deepcopy
import json

import pytest


def test_request_copies_input_and_output(sdk, report_request):
    original = deepcopy(report_request)
    builder = sdk.RequestCreator(report_request)
    builder.addMetric("metrics/revenue")
    assert report_request == original
    output = builder.to_dict()
    output["metricContainer"]["metrics"].clear()
    assert builder.getMetrics() == ["metrics/pageviews", "metrics/revenue"]


def test_request_instances_do_not_share_template(sdk):
    first = sdk.RequestCreator()
    second = sdk.RequestCreator()
    first.addMetric("metrics/pageviews")
    first.addGlobalFilter("segment-1")
    assert second.to_dict()["metricContainer"]["metrics"] == []
    assert second.to_dict()["globalFilters"] == []


def test_metric_column_ids_and_default_sort(sdk):
    builder = sdk.RequestCreator()
    builder.addMetric("metrics/pageviews")
    builder.addMetric("metrics/revenue")
    assert builder.to_dict()["metricContainer"]["metrics"] == [
        {"id": "metrics/pageviews", "columnId": "0", "sort": "desc"},
        {"id": "metrics/revenue", "columnId": "1"},
    ]


@pytest.mark.parametrize("sort_first", [True, False])
def test_dimension_sort_removes_metric_sort(sdk, sort_first):
    builder = sdk.RequestCreator()
    if sort_first:
        builder.setDimensionSort("asc")
    builder.addMetric("metrics/pageviews")
    if not sort_first:
        builder.setDimensionSort("asc")
    request = builder.to_dict()
    assert request["settings"]["dimensionSort"] == "asc"
    assert "sort" not in request["metricContainer"]["metrics"][0]


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {
            "metricId": "metrics/pageviews",
            "metricDefinition": {"func": "number", "val": 1},
        },
        {"metricId": "metrics/pageviews", "attributionModel": "unsupported"},
        {
            "metricId": "metrics/pageviews",
            "attributionModel": "linear",
            "lookbackWindow": 0,
        },
        {
            "metricId": "metrics/pageviews",
            "attributionModel": "linear",
            "lookbackWindow": 91,
        },
        {"metricId": "cm1@AdobeOrg", "attributionModel": "linear"},
    ],
)
def test_invalid_metric_definitions_are_rejected(sdk, arguments):
    builder = sdk.RequestCreator()
    with pytest.raises(ValueError):
        builder.addMetric(**arguments)
    assert builder.getMetrics() == []


@pytest.mark.parametrize("sampling", [-0.01, 1.01])
def test_sampling_bounds(sdk, sampling):
    with pytest.raises(ValueError, match="between 0 and 1"):
        sdk.RequestCreator().setSampling(sampling)


def test_sampling_and_upsampling(sdk):
    builder = sdk.RequestCreator()
    builder.setSampling(0.25, upsample=True)
    assert builder.to_dict()["settings"]["sampling"] == 0.25
    assert builder.to_dict()["settings"]["samplingUpSample"] is True


def test_date_range_replaces_previous_dates_but_preserves_segments(sdk):
    builder = sdk.RequestCreator()
    builder.addGlobalFilter("segment-1")
    builder.setDateRange("2025-01-01", "2025-01-31")
    builder.setDateRange("2025-02-01", "2025-02-28")
    assert builder.to_dict()["globalFilters"] == [
        {"type": "segment", "segmentId": "segment-1"},
        {
            "type": "dateRange",
            "dateRange": "2025-02-01T00:00:00.000/2025-02-28T23:59:59.999",
        },
    ]


@pytest.mark.parametrize(
    "filter_id,expected",
    [
        ("segment-1", {"type": "segment", "segmentId": "segment-1"}),
        (
            "2025-01-01T00:00:00.000/2025-02-01T00:00:00.000",
            {
                "type": "dateRange",
                "dateRange": "2025-01-01T00:00:00.000/2025-02-01T00:00:00.000",
            },
        ),
        (
            "variables/page:::123",
            {"type": "breakdown", "dimension": "variables/page", "itemId": "123"},
        ),
    ],
)
def test_global_filter_shapes(sdk, filter_id, expected):
    builder = sdk.RequestCreator()
    builder.addGlobalFilter(filter_id)
    assert builder.to_dict()["globalFilters"] == [expected]


def test_request_save_and_load_round_trip(sdk, report_request, tmp_path):
    path = tmp_path / "request.json"
    sdk.RequestCreator(report_request).save(str(path))
    restored = sdk.RequestCreator(str(path))
    assert restored.to_dict() == report_request
    assert json.loads(str(restored)) == report_request


def test_search_can_be_replaced_and_removed(sdk):
    builder = sdk.RequestCreator()
    builder.setSearch(itemIds=["123"])
    assert builder.to_dict()["search"] == {"itemIds": ["123"]}
    builder.setSearch(clause="CONTAINS 'home'")
    assert builder.to_dict()["search"] == {"clause": "CONTAINS 'home'"}
    builder.removeSearch()
    assert "search" not in builder.to_dict()
    assert builder.search is False


def test_date_range_update_on_new_request(sdk):
    builder = sdk.RequestCreator()
    date_range = "2025-01-01T00:00:00.000/2025-02-01T00:00:00.000"
    builder.updateDateRange(dateRange=date_range)
    assert builder.to_dict()["globalFilters"] == [
        {"type": "dateRange", "dateRange": date_range},
    ]
