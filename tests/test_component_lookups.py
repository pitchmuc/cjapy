"""Single dimension and metric lookups, checked against a real org.

getDimensions and getMetrics return IDs with a prefix ("variables/..." and
"metrics/..."). The single-item endpoints answer 404 for those IDs and only
accept the ID without the prefix. The metric endpoint also rejects the
dimension-only expansions (bucketingSetting, noValueOptionsSetting,
defaultDimensionSort, persistenceSetting) with "invalid_data", while the
dimension endpoint accepts them.
"""

import pytest


DIMENSION_ONLY_EXPANSIONS = {
    "bucketingSetting",
    "noValueOptionsSetting",
    "defaultDimensionSort",
    "persistenceSetting",
}


@pytest.mark.parametrize("dimension_id", ["variables/page", "page"])
def test_get_dimension_accepts_listed_and_bare_ids(client, queued_pages, dimension_id):
    calls = queued_pages([{"id": "variables/page"}])
    client.getDimension("dv-1", dimension_id)
    assert calls[0][0] == "https://cja.adobe.io/data/dataviews/dv-1/dimensions/page"


@pytest.mark.parametrize("metric_id", ["metrics/visits", "visits"])
def test_get_metric_accepts_listed_and_bare_ids(client, queued_pages, metric_id):
    calls = queued_pages([{"id": "metrics/visits"}])
    client.getMetric("dv-1", metric_id)
    assert calls[0][0] == "https://cja.adobe.io/data/dataviews/dv-1/metrics/visits"


def test_get_metric_full_leaves_out_dimension_only_expansions(client, queued_pages):
    calls = queued_pages([{"id": "metrics/visits"}])
    client.getMetric("dv-1", "visits", full=True)
    expansions = set(calls[0][1]["params"]["expansion"].split(","))
    assert expansions.isdisjoint(DIMENSION_ONLY_EXPANSIONS)


def test_get_dimension_full_requests_dimension_settings(client, queued_pages):
    calls = queued_pages([{"id": "variables/page"}])
    client.getDimension("dv-1", "page", full=True)
    expansions = set(calls[0][1]["params"]["expansion"].split(","))
    assert DIMENSION_ONLY_EXPANSIONS <= expansions
