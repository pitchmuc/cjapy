"""Optional Pydantic models (cjapy[models]); see issue #32.

The JSON files in tests/fixtures/cja/ were recorded from a real organization
with scripts/record_fixtures.py. Every string value except API enums was
replaced with a placeholder, so the values are not real, but the field names,
value types and nesting are what the API sends.
"""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

pydantic = pytest.importorskip("pydantic")
models = pytest.importorskip("cjapy.models")

FIXTURES = Path(__file__).parent / "fixtures" / "cja"


def load(name):
    return json.loads((FIXTURES / name).read_text())


def rows(name):
    return [row for page in load(name) for row in page["content"]]


RECORDED = [
    ("DataView", rows("dataviews_pages.json") + [load("dataview.json")]),
    ("Dimension", rows("dimensions_pages.json") + [load("dimension.json")]),
    ("Metric", rows("metrics_pages.json") + [load("metric.json")]),
]


@pytest.mark.parametrize("model_name,records", RECORDED, ids=[r[0] for r in RECORDED])
def test_recorded_responses_validate(model_name, records):
    model = getattr(models, model_name)
    assert records
    for record in records:
        item = model.model_validate(record)
        assert item.id == record["id"]
        # Nothing is lost: dumping gives back the recorded response.
        assert item.model_dump(exclude_unset=True) == record


@pytest.mark.parametrize("model_name,records", RECORDED, ids=[r[0] for r in RECORDED])
def test_models_declare_every_recorded_field(model_name, records):
    """A recorded field that the model does not declare would land in model_extra."""
    model = getattr(models, model_name)
    undeclared = {key for record in records for key in model.model_validate(record).model_extra}
    assert undeclared == set()


def test_unknown_fields_are_kept():
    item = models.DataView.model_validate({"id": "dv_1", "brandNewField": {"a": 1}})
    assert item.model_extra == {"brandNewField": {"a": 1}}
    assert item.model_dump()["brandNewField"] == {"a": 1}


def test_only_id_is_required():
    assert models.Metric.model_validate({"id": "metrics/visits"}).name is None
    with pytest.raises(pydantic.ValidationError):
        models.Dimension.model_validate({"name": "no id"})


def test_curation_enabled_keeps_the_string_the_api_sends():
    assert models.DataView.model_validate(load("dataview.json")).curationEnabled == "true"


@pytest.mark.parametrize(
    "method,arguments,fixture,model_name",
    [
        ("getDataViews", {}, "dataviews_pages.json", "DataView"),
        ("getDimensions", {"dataviewId": "dv_1"}, "dimensions_pages.json", "Dimension"),
        ("getMetrics", {"dataviewId": "dv_1"}, "metrics_pages.json", "Metric"),
    ],
)
def test_list_methods_return_models(client, queued_pages, method, arguments, fixture, model_name):
    page = load(fixture)[0]
    # One page only. getDataViews reads "last" until the fix in #34, so send both keys.
    queued_pages([dict(page, last=True, lastPage=True)])
    result = getattr(client, method)(output="model", **arguments)
    assert [type(item).__name__ for item in result] == [model_name] * len(page["content"])
    assert [item.id for item in result] == [row["id"] for row in page["content"]]


def test_df_and_raw_outputs_are_unchanged(client, queued_pages):
    page = load("metrics_pages.json")[0]
    queued_pages([page, page])
    assert client.getMetrics("dv_1", output="raw") == page["content"]
    assert client.getMetrics("dv_1")["id"].tolist() == [row["id"] for row in page["content"]]


def test_import_cjapy_does_not_import_pydantic():
    code = textwrap.dedent(
        """
        import sys
        import cjapy
        assert "pydantic" not in sys.modules, "import cjapy loaded pydantic"
        assert "cjapy.models" not in sys.modules
        """
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_models_explain_the_extra_when_pydantic_is_missing():
    code = textwrap.dedent(
        """
        import sys
        sys.modules["pydantic"] = None
        try:
            import cjapy.models
        except ImportError as error:
            assert "pip install cjapy[models]" in str(error), error
        else:
            raise AssertionError("cjapy.models imported without pydantic")
        """
    )
    subprocess.run([sys.executable, "-c", code], check=True)
