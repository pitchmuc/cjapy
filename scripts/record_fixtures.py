"""Record scrubbed CJA API responses for use as test fixtures.

Run this yourself with your own credentials. It makes read-only GET requests:

    python scripts/record_fixtures.py --config myconfig.json --dataview dv_123

It calls cjapy's own methods (getDataViews, getDataView, getDimensions,
getDimension, getMetrics, getMetric) with full=True, and records the raw pages
the API returns for those calls. So the fixtures match exactly what cjapy
requests, including its expansion lists.

Before saving, every string value is replaced with a placeholder, except for
values under keys listed in KEEP_KEYS, e.g. "type". The same input string always
gets the same placeholder, so IDs still match across files. Numbers, booleans,
nulls and the response keys themselves are kept. Lists of rows are cut to
--max-rows entries.

The files go to tests/fixtures/recorded/, which git ignores. Check them by hand,
then copy the ones you want to keep to tests/fixtures/cja/.
"""

import argparse
import json
from copy import deepcopy
from pathlib import Path

import cjapy


# Keys whose string values are API enums rather than customer data.
KEEP_KEYS = {
    "type", "dataType", "schemaType", "sourceFieldType", "dataSetType",
    "polarity", "precision", "includeType", "componentType", "timezoneDesignator",
    "containerNames", "bucketingSetting", "noValueOptionsSetting", "persistenceSetting",
    "defaultDimensionSort", "includeExcludeSetting", "fieldDefinition", "allocation",
    "expiration", "granularity", "func", "sortOrder", "segmentable", "status",
    "curationEnabled", "model",
}

PAGE_KEYS = ("last", "lastPage", "first", "firstPage", "number", "numberOfElements",
             "size", "totalElements", "totalPages")

# Returned once the page budget is spent, so cjapy's paging loops stop.
STOP_PAGE = {"content": [], "last": True, "lastPage": True}


class RecordingConnector:
    """Wrap a cjapy connector and keep the raw responses of GET requests."""

    def __init__(self, connector, max_pages):
        self.connector = connector
        self.max_pages = max_pages
        self.responses = []

    def getData(self, url, *args, **kwargs):
        if len(self.responses) >= self.max_pages:
            return dict(STOP_PAGE)
        response = self.connector.getData(url, *args, **kwargs)
        if isinstance(response, dict) and "errorCode" in response:
            raise SystemExit(
                f"API error for {url}: {response.get('errorCode')}: {response.get('errorDescription')}"
            )
        # cjapy extends the first page's content list in place while paging,
        # so keep a copy of what the API sent.
        self.responses.append(deepcopy(response))
        return response

    def __getattr__(self, name):
        return getattr(self.connector, name)


def record(cja, method, max_pages, *args, **kwargs):
    """Call a cjapy method and return the raw responses it received."""
    original = cja.connector
    recorder = RecordingConnector(original, max_pages)
    cja.connector = recorder
    try:
        getattr(cja, method)(*args, **kwargs)
    finally:
        cja.connector = original
    return recorder.responses


class Scrubber:
    def __init__(self, max_rows=25):
        self.mapping = {}
        self.max_rows = max_rows

    def placeholder(self, value):
        if value not in self.mapping:
            self.mapping[value] = "str_{}".format(len(self.mapping) + 1)
        return self.mapping[value]

    def scrub(self, value, key=None):
        if isinstance(value, dict):
            return {k: self.scrub(v, k) for k, v in value.items()}
        if isinstance(value, list):
            if key == "content":
                value = value[: self.max_rows]
            # Lists of enum values (e.g. containerNames) keep the parent key's rule.
            return [self.scrub(v, key) for v in value]
        if isinstance(value, str):
            if key in KEEP_KEYS:
                return value
            return self.placeholder(value)
        return value


def page_keys(responses):
    return [{k: r.get(k) for k in PAGE_KEYS if k in r} for r in responses if isinstance(r, dict)]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, type=Path, help="cjapy config JSON file")
    parser.add_argument("--dataview", required=True, help="data view ID to record")
    parser.add_argument("--out", type=Path, default=Path("tests/fixtures/recorded"))
    parser.add_argument("--page-size", type=int, default=2, help="data views per page")
    parser.add_argument("--max-rows", type=int, default=25, help="rows kept per page")
    args = parser.parse_args()

    cjapy.importConfigFile(str(args.config))
    cja = cjapy.CJA()
    dv = args.dataview

    raw = {
        # Two small pages, so the fixture shows how pages link together.
        "dataviews_pages": record(cja, "getDataViews", 2, limit=args.page_size, full=True, output="raw"),
        "dataview": record(cja, "getDataView", 1, dv, full=True)[0],
        # The dimensions and metrics endpoints ignore limit and return one page.
        "dimensions_pages": record(cja, "getDimensions", 1, dv, full=True, output="raw"),
        "metrics_pages": record(cja, "getMetrics", 1, dv, full=True, output="raw"),
    }
    first_dimension = (raw["dimensions_pages"][0].get("content") or [{}])[0].get("id")
    first_metric = (raw["metrics_pages"][0].get("content") or [{}])[0].get("id")
    if first_dimension:
        raw["dimension"] = record(cja, "getDimension", 1, dv, first_dimension, full=True)[0]
    if first_metric:
        raw["metric"] = record(cja, "getMetric", 1, dv, first_metric, full=True)[0]

    print("Pagination keys seen (before scrubbing):")
    for name in ("dataviews_pages", "dimensions_pages", "metrics_pages"):
        print(" ", name, page_keys(raw[name]))

    scrubber = Scrubber(args.max_rows)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, value in raw.items():
        path = args.out / f"{name}.json"
        path.write_text(json.dumps(scrubber.scrub(value), indent=2, sort_keys=True) + "\n")
        print("wrote", path)
    print(f"Replaced {len(scrubber.mapping)} distinct strings. Review the files before committing.")


if __name__ == "__main__":
    main()
