"""Data view component methods, tested against a fake connector (no HTTP)."""

import pytest

import cjapy


class FakeConnector:
    """Return scripted pages per path and record each request's params."""

    def __init__(self, pages):
        self.pages = {path: list(items) for path, items in pages.items()}
        self.calls = []

    def getData(self, endpoint, params=None, **kwargs):
        path = endpoint.split("/data", 1)[1]
        self.calls.append((path, dict(params or {})))
        pages = self.pages[path]
        page = (params or {}).get("page", 0)
        return pages[min(page, len(pages) - 1)]


@pytest.fixture
def make_cja():
    def make(pages):
        cja = cjapy.CJA(
            config_object={
                "org_id": "test-org",
                "token": "not-a-real-token",
                "date_limit": float("inf"),
            }
        )
        cja.connector.session.close()
        cja.connector = FakeConnector(pages)
        return cja

    return make


def two_pages(prefix):
    return [
        {"content": [{"id": prefix + "1"}], "lastPage": False},
        {"content": [{"id": prefix + "2"}], "lastPage": True},
    ]


@pytest.mark.parametrize(
    "method, kind", [("getMetrics", "metrics"), ("getDimensions", "dimensions")]
)
def test_raw_output_returns_every_page(make_cja, method, kind):
    path = "/dataviews/dv_1/" + kind
    cja = make_cja({path: two_pages(kind[0])})

    result = getattr(cja, method)("dv_1", output="raw")

    assert result == [{"id": kind[0] + "1"}, {"id": kind[0] + "2"}]
    assert [params["page"] for _, params in cja.connector.calls] == [0, 1]


@pytest.mark.parametrize(
    "method, kind", [("getMetrics", "metrics"), ("getDimensions", "dimensions")]
)
def test_df_output_returns_every_page(make_cja, method, kind):
    cja = make_cja({"/dataviews/dv_1/" + kind: two_pages(kind[0])})

    df = getattr(cja, method)("dv_1")

    assert df["id"].tolist() == [kind[0] + "1", kind[0] + "2"]


def test_shared_components_matrix_includes_hidden_components(make_cja):
    shared = {"sharedComponent": True}
    cja = make_cja(
        {
            "/dataviews": [{"content": [{"id": "dv_1", "name": "Main"}], "last": True}],
            "/dataviews/dv_1/dimensions": [
                {"content": [{"id": "d1", "name": "Page", **shared}], "lastPage": True}
            ],
            "/dataviews/dv_1/metrics": [
                {"content": [{"id": "m1", "name": "Visits", **shared}], "lastPage": True}
            ],
        }
    )

    df = cja.getSharedComponentsMatrix()

    component_calls = [params for path, params in cja.connector.calls if path != "/dataviews"]
    assert len(component_calls) == 2
    assert all(params.get("includeType") == "hidden" for params in component_calls)
    assert df.loc["d1", "Main"] == 1
    assert df.loc["m1", "Main"] == 1


def test_get_metric_requires_metric_id(make_cja):
    cja = make_cja({})

    with pytest.raises(ValueError, match="Require a Metric ID"):
        cja.getMetric("dv_1")
