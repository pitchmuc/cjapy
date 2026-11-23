# cjapy models

cjapy can return typed [Pydantic](https://docs.pydantic.dev/) objects instead of dictionaries or DataFrames. This is optional.

## Install

```shell
pip install cjapy[models]
```

A plain `pip install cjapy` does not install Pydantic, and `import cjapy` does not load it. Pydantic 2 is required.

## Use

Ask a list method for models with `output="model"`:

```python
import cjapy

cjapy.importConfigFile("myconfig.json")
cja = cjapy.CJA()

dataviews = cja.getDataViews(output="model")          # list of DataView
dimensions = cja.getDimensions("dv_123", full=True, output="model")  # list of Dimension
metrics = cja.getMetrics("dv_123", full=True, output="model")        # list of Metric

for dimension in dimensions:
    print(dimension.id, dimension.name, dimension.hidden)
```

`output="df"` (the default) and `output="raw"` work as before.

You can also validate any response yourself:

```python
from cjapy.models import DataView

dataview = DataView.model_validate(cja.getDataView("dv_123"))
```

## Models

| Model | Returned by |
|---|---|
| `DataView` | `getDataViews`, `getDataView` |
| `Dimension` | `getDimensions`, `getDimension` |
| `Metric` | `getMetrics`, `getMetric` |

`Dimension` and `Metric` share the fields of `Component`. All models derive from `CJAModel`.

## Permissive by design

The CJA API changes often, so the models do not break when it does:

* Only `id` is required. Every other field is optional, because the API leaves fields out when they are not set or were not requested.
* Fields that a model does not declare are kept. Read them with `model.model_extra`, and `model.model_dump()` includes them.
* Nested objects, such as `owner`, settings and `usageSummary`, stay plain dictionaries for now.

The field names and types come from responses recorded from a real organization, not only from the API documentation. For example, `curationEnabled` on a data view is the string `"true"` or `"false"`, not a boolean, and `defaultDimensionSort` on a dimension is a boolean.

## Test fixtures

`tests/fixtures/cja/` holds responses recorded with `scripts/record_fixtures.py`. The script calls cjapy's own methods, records the raw pages the API returns, and replaces every string value with a placeholder except API enum values. The tests check that every recorded row validates and that the models declare every recorded field.

To record new fixtures from your own organization:

```shell
python scripts/record_fixtures.py --config myconfig.json --dataview dv_123
```

The files go to `tests/fixtures/recorded/`, which git ignores. Check them by hand before you copy any to `tests/fixtures/cja/`.
