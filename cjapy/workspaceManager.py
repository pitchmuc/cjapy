"""Offline, lossless CJA Workspace parsing and composable project builders.

The public builder API follows aanalytics2.workspaceManager. CJA's project root
uses dataId, while panels still use Adobe's ReportSuite/rsid wire vocabulary.
"""

import json
import uuid
import warnings
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

__all__ = [
    "WorkspaceManager",
    "WorkspaceDefinition",
    "Panel",
    "FreeForm",
    "TextBuilder",
    "Reportlet",
    "FreeformReportlet",
    "TextReportlet",
    "SectionHeaderReportlet",
    "SummaryNumberReportlet",
    "SummaryChangeReportlet",
    "LineReportlet",
    "BarReportlet",
    "HorizontalBarReportlet",
    "BarStackedReportlet",
    "HorizontalBarStackedReportlet",
    "AreaReportlet",
    "AreaStackedReportlet",
    "DonutReportlet",
    "ScatterReportlet",
    "TreemapReportlet",
    "HistogramReportlet",
    "BulletReportlet",
    "VennReportlet",
    "ComboReportlet",
    "KeyMetricSummaryReportlet",
    "Flow",
    "Fallout",
    "CohortReportlet",
    "JourneyCanvasReportlet",
    "MapReportlet",
]

_COMPONENT_ATTRS = (
    "dimensions",
    "dimensionItems",
    "metrics",
    "calculatedMetrics",
    "segments",
    "dateRanges",
    "dataViews",
    "annotations",
    "attributionTemplates",
)
_COMPONENT_TYPES = {
    "Dimension": "dimensions",
    "DimensionItem": "dimensionItems",
    "Metric": "metrics",
    "CalculatedMetric": "calculatedMetrics",
    "Segment": "segments",
    "Segments": "segments",
    "Filter": "segments",
    "DateRange": "dateRanges",
    "ReportSuite": "dataViews",
    "DataView": "dataViews",
    "Annotation": "annotations",
    "AttributionTemplate": "attributionTemplates",
}
_COLORS = [
    "#26C0C7",
    "#5151D3",
    "#E68619",
    "#D83790",
    "#908DFA",
    "#58E06F",
    "#2780EB",
    "#6F38B1",
    "#DFBF03",
    "#CB6F10",
    "#268D6C",
    "#9BEC54",
    "#5EABFA",
    "#BE40CC",
    "#F56BB7",
    "#FEE02D",
]
_VIZ_TYPE_MAP = {
    "line": "LineReportlet",
    "bar": "BarReportlet",
    "bar_horizontal": "HorizontalBarReportlet",
    "bar_stacked": "BarStackedReportlet",
    "bar_horizontal_stacked": "HorizontalBarStackedReportlet",
    "area": "AreaReportlet",
    "area_stacked": "AreaStackedReportlet",
    "donut": "DonutReportlet",
    "scatter": "ScatterReportlet",
    "treemap": "TreemapReportlet",
    "histogram": "HistogramReportlet",
    "bullet": "BulletReportlet",
    "venn": "VennReportlet",
    "combo": "ComboReportlet",
}


def _uuid() -> str:
    return str(uuid.uuid4()).upper()


def _component(id_: str, name: str, type_: str) -> dict:
    return {
        "id": id_,
        "__entity__": True,
        "type": type_,
        "__metaData__": {"name": name},
    }


def _detect_component_type(item_id: str) -> str:
    if "::" in item_id:
        return "DimensionItem"
    if item_id.startswith("cm"):
        return "CalculatedMetric"
    if item_id.startswith("metrics/"):
        return "Metric"
    if item_id.startswith(("variables/", "_")):
        return "Dimension"
    return "Segment"


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _components(value: Any) -> dict[str, list[dict]]:
    collected: dict[str, dict[str, dict]] = {key: {} for key in _COMPONENT_ATTRS}

    def register(cid: Any, type_: str, name: str = None) -> None:
        target = _COMPONENT_TYPES.get(type_)
        if target is None or not isinstance(cid, str) or not cid:
            return
        entry = {"id": cid, "name": name or cid}
        collected[target].setdefault(cid, entry)
        if target == "dimensionItems":
            collected["dimensions"].setdefault(cid, entry)

    for comp in _walk(value):
        type_ = comp.get("type")
        target = _COMPONENT_TYPES.get(type_) if isinstance(type_, str) else None
        cid = comp.get("id")
        if target:
            register(cid, type_, (comp.get("__metaData__") or {}).get("name"))
        # Guided Analysis uses explicit reference fields instead of entity objects.
        for field, ref_type in (
            ("metricId", "Metric"),
            ("segmentId", "Segment"),
            ("dimensionId", "Dimension"),
        ):
            ref_id = comp.get(field)
            if (
                field == "metricId"
                and isinstance(ref_id, str)
                and ref_id.startswith("cm")
            ):
                ref_type = "CalculatedMetric"
            register(
                ref_id,
                ref_type,
                comp.get("dimensionName")
                if field == "dimensionId"
                else comp.get("name"),
            )
        if isinstance(comp.get("dimensionId"), str):
            for item in comp.get("dimensionItems", []) or []:
                item_id = item.get("itemId") if isinstance(item, dict) else item
                if isinstance(item_id, str):
                    register(
                        f"{comp['dimensionId']}::{item_id}",
                        "DimensionItem",
                        item.get("value") if isinstance(item, dict) else item_id,
                    )
    return {key: list(items.values()) for key, items in collected.items()}


def _merge(*summaries: dict[str, list[dict]]) -> dict[str, list[dict]]:
    result = {key: {} for key in _COMPONENT_ATTRS}
    for summary in summaries:
        for key in _COMPONENT_ATTRS:
            for comp in summary[key]:
                result[key].setdefault(comp["id"], comp)
    return {key: list(items.values()) for key, items in result.items()}


class _ComponentView:
    def _set_components(self, summary: dict[str, list[dict]]) -> None:
        for key, values in summary.items():
            setattr(self, key, values)

    @property
    def filters(self) -> list[dict]:
        return self.segments

    @property
    def components(self) -> dict[str, list[dict]]:
        return {key: getattr(self, key) for key in _COMPONENT_ATTRS}


def _search() -> dict:
    return {"alwaysExcludedItems": [], "operator": "AND", "rules": []}


def _cell_display() -> dict:
    return {
        "conditionalFormattingOpts": {
            "autoGenerate": True,
            "colorPalette": "#ffa48c,#ffcb94,#fff19b,#cadf7d,#95cc5f",
            "usePercentLimits": False,
        },
        "location": "behindNumber",
        "type": {
            "background": True,
            "backgroundType": "bar",
            "comparison": "none",
            "interpretZeroAsNoValue": False,
            "number": True,
            "percent": True,
            "showAnomaly": False,
            "showForecasting": False,
            "showGrandTotal": True,
            "showSparklines": True,
            "showTotals": True,
            "wrapHeaderText": True,
        },
    }


def _column_node(comp: dict | None = None, nodes: list[dict] | None = None) -> dict:
    node = {
        "_computedValues": [],
        "dataSettings": {
            "advancedItemLimit": 5,
            "advancedItemSearch": _search(),
        },
        "id": str(uuid.uuid4()),
        "name": "",
        "nodes": nodes or [],
        "selectionCoordinates": [],
        "tableCellDisplay": _cell_display(),
        "visible": True,
    }
    if comp is not None:
        node["component"] = comp
        node["name"] = comp["__metaData__"]["name"]
    return node


def _static_row(item: dict) -> dict:
    return {
        "id": uuid.uuid4().hex[:9],
        "component": _component(
            item["id"],
            item.get("name", item["id"]),
            item.get("type") or _detect_component_type(item["id"]),
        ),
        "dataSettings": {"advancedItemLimit": 5, "advancedItemSearch": _search()},
    }


def _positive_rows(rows: int) -> None:
    if isinstance(rows, bool) or not isinstance(rows, int) or rows < 1:
        raise ValueError("rows must be a positive integer.")


def _new_freeform_table(
    column_tree: dict,
    rows: int,
    dim_id: str = None,
    dim_name: str = None,
    items: list[dict] = None,
) -> dict:
    _positive_rows(rows)
    nodes = column_tree.get("nodes", [])
    column_id = next(
        (
            node["id"]
            for node in _walk(nodes)
            if (node.get("component") or {}).get("type")
            in ("Metric", "CalculatedMetric")
        ),
        nodes[0]["id"] if nodes else "",
    )
    table = {
        "alignDatesForTimeDimension": True,
        "attributionSettings": [],
        "breakdowns": [],
        "collapsed": False,
        "columnWidths": [100.0] * (len(nodes) + 1),
        "hyperlinks": [],
        "pagination": {"currentPage": 0, "viewBy": rows},
        "parentItemIds": [],
        "selectionCoordinates": [],
        "settings": {
            "breakdownByPosition": False,
            "rowBasedPercentages": False,
            "showThumbnails": False,
            "totalsType": "allVisits" if dim_id else "columnSum",
        },
        "sort": {
            "advancedSortRules": [],
            "asc": False,
            "columnId": column_id,
            "labelColumn": False,
        },
        "staticRows": [_static_row(item) for item in items or []],
        "staticSearch": _search(),
        "statistics": {"functions": [], "ignoreZeros": True},
    }
    if dim_id:
        table["dimensionSettings"] = [
            {
                "id": uuid.uuid4().hex[:6],
                "dimension": _component(dim_id, dim_name or dim_id, "Dimension"),
                "search": _search(),
            }
        ]
    return table


class TextBuilder:
    """Compose the Quill Delta JSON used by CJA and Analytics TextReportlets."""

    def __init__(self):
        self._ops: list[dict] = []

    def addTitle(self, text: str, level: int = 2) -> "TextBuilder":
        if isinstance(level, bool) or level not in range(1, 7):
            raise ValueError("Heading level must be between 1 and 6.")
        self.addText(text)
        self._ops.append({"attributes": {"header": level}, "insert": "\n"})
        return self

    def addText(self, text: str) -> "TextBuilder":
        self._ops.append({"insert": text})
        return self

    def _styled(self, text: str, **attributes: Any) -> "TextBuilder":
        self._ops.append({"attributes": attributes, "insert": text})
        return self

    def addBold(self, text: str) -> "TextBuilder":
        return self._styled(text, bold=True)

    def addItalic(self, text: str) -> "TextBuilder":
        return self._styled(text, italic=True)

    def addUnderline(self, text: str) -> "TextBuilder":
        return self._styled(text, underline=True)

    def addColor(self, text: str, color: str) -> "TextBuilder":
        return self._styled(text, color=color)

    def addLink(self, text: str, url: str) -> "TextBuilder":
        return self._styled(text, link=url)

    def addNewline(self) -> "TextBuilder":
        return self.addText("\n")

    def to_dict(self) -> dict:
        return {"ops": deepcopy(self._ops)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def __str__(self) -> str:
        return self.to_json()

    __repr__ = __str__


class Reportlet(_ComponentView):
    """A typed reportlet with lossless raw JSON and component references."""

    def __init__(self, raw: dict | None = None):
        self.raw = deepcopy(raw or {})
        self.type = self.raw.get("type", type(self).__name__)
        self.name = self.raw.get("name", "")
        self._set_components(_components(self.raw))

    def to_dict(self) -> dict:
        return deepcopy(self.raw)

    def __getattr__(self, name: str) -> Any:
        raw = self.__dict__.get("raw", {})
        if name in raw:
            return raw[name]
        raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")

    @classmethod
    def from_dict(cls, raw: dict) -> "Reportlet":
        reportlet_class = _REPORTLET_CLASSES.get(raw.get("type"), cls)
        if reportlet_class is FreeForm:
            return FreeForm.from_dict(raw)
        return reportlet_class(raw)

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    __repr__ = __str__


class TextReportlet(Reportlet):
    def __init__(self, raw: dict | None = None):
        super().__init__(raw)
        content = self.raw.get("textContent")
        self.textOps: list[dict] = []
        self.parseWarnings: list[str] = []
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                self.parseWarnings.append("textContent is not valid Quill Delta JSON.")
                content = {"ops": [{"insert": content}]}
        if isinstance(content, dict):
            ops = content.get("ops", [])
            if isinstance(ops, list):
                self.textOps = ops
            else:
                self.parseWarnings.append("Quill Delta ops must be a list.")
        elif content is not None:
            self.parseWarnings.append("textContent is not a Quill Delta object.")
        self.text = "".join(
            op["insert"]
            for op in self.textOps
            if isinstance(op, dict) and isinstance(op.get("insert"), str)
        )


class SectionHeaderReportlet(TextReportlet):
    def __init__(self, raw: dict | None = None):
        super().__init__(raw)
        if "textContent" not in self.raw:
            self.text = self.name


class SummaryNumberReportlet(Reportlet):
    pass


class SummaryChangeReportlet(Reportlet):
    pass


class LineReportlet(Reportlet):
    pass


class BarReportlet(Reportlet):
    pass


class HorizontalBarReportlet(Reportlet):
    pass


class BarStackedReportlet(Reportlet):
    pass


class HorizontalBarStackedReportlet(Reportlet):
    pass


class AreaReportlet(Reportlet):
    pass


class AreaStackedReportlet(Reportlet):
    pass


class DonutReportlet(Reportlet):
    pass


class ScatterReportlet(Reportlet):
    pass


class TreemapReportlet(Reportlet):
    pass


class HistogramReportlet(Reportlet):
    pass


class BulletReportlet(Reportlet):
    pass


class VennReportlet(Reportlet):
    pass


class ComboReportlet(Reportlet):
    pass


class KeyMetricSummaryReportlet(Reportlet):
    pass


class Flow(Reportlet):
    pass


class Fallout(Reportlet):
    pass


class CohortReportlet(Reportlet):
    pass


class JourneyCanvasReportlet(Reportlet):
    pass


class MapReportlet(Reportlet):
    pass


class FreeForm(Reportlet):
    """A freeform table, including multi-dimension rows and nested breakdowns."""

    def __init__(self, title: str = ""):
        super().__init__({"type": "FreeformReportlet", "name": title})
        self.title = title
        self.dimension: dict | None = None
        self.dimensionSettings: list[dict] = []
        self.staticRows: list[dict] = []
        self.breakdowns: list[FreeForm] = []
        self.columnTree: dict = {}
        self.parentItemId: str | None = None
        self.parentItemIds: list[str] = []
        self.breakdownByPosition = False
        self._table: dict = {}
        self._is_breakdown = False
        self._sync: Callable[[], None] | None = None

    @classmethod
    def build(
        cls,
        title: str,
        metrics: list[dict],
        dim_id: str = None,
        dim_name: str = None,
        items: list[dict] = None,
        rows: int = 10,
    ) -> "FreeForm":
        _positive_rows(rows)
        if not metrics:
            raise ValueError("At least one metric is required.")
        if bool(dim_id) == bool(items):
            raise ValueError(
                "Provide either a dimension or non-empty static items, not both."
            )
        nodes = []
        for metric in metrics:
            mid = metric["id"]
            base = _column_node(
                _component(
                    mid,
                    metric.get("name", mid),
                    metric.get("type")
                    or ("CalculatedMetric" if mid.startswith("cm") else "Metric"),
                )
            )
            filters = metric.get("filters", [])
            dim_filters = [f for f in filters if f.get("type") == "DimensionItem"]
            base["nodes"] = [
                _column_node(
                    _component(
                        f["id"], f.get("name", f["id"]), f.get("type", "Segment")
                    )
                )
                for f in filters
                if f.get("type") != "DimensionItem"
            ]
            if dim_filters:
                for filter_ in dim_filters:
                    inner = deepcopy(base)
                    # Copies must have unique descendant IDs as well as a unique root.
                    for node in _walk(inner):
                        if "nodes" in node and "id" in node:
                            node["id"] = str(uuid.uuid4())
                    nodes.append(
                        _column_node(
                            _component(
                                filter_["id"],
                                filter_.get("name", filter_["id"]),
                                "DimensionItem",
                            ),
                            [inner],
                        )
                    )
            else:
                nodes.append(base)
        column_tree = _column_node(nodes=nodes)
        table = _new_freeform_table(column_tree, rows, dim_id, dim_name, items)
        return cls.from_dict(
            {
                "advancedMode": False,
                "advancedSettings": {"rows": [], "tableState": "builder"},
                "columnTree": column_tree,
                "freeformTable": table,
                "hideTitle": False,
                "intelligentCaptions": {
                    "captions": [],
                    "hasLoaded": False,
                    "hiddenCaptions": [],
                    "isExpanded": False,
                },
                "isConfigVisible": True,
                "isReadOnly": False,
                "name": title,
                "showAnnotations": True,
                "showControls": True,
                "type": "FreeformReportlet",
            }
        )

    @classmethod
    def from_dict(cls, reportlet: dict) -> "FreeForm":
        ff = cls(reportlet.get("name", ""))
        ff.raw = deepcopy(reportlet)
        ff.columnTree = ff.raw.get("columnTree", {}) or {}
        ff._load_table(ff.raw.get("freeformTable", {}) or {})
        ff._recompute_summaries()
        return ff

    def _load_table(self, table: dict) -> None:
        self._table = deepcopy(table)
        self.dimensionSettings = self._table.get("dimensionSettings", []) or []
        dims = [s["dimension"] for s in self.dimensionSettings if s.get("dimension")]
        if not dims:
            dims = self._table.get("dimensions", []) or []
        if not dims and self._table.get("dimension"):
            dims = [self._table["dimension"]]
        self.dimension = dims[0] if dims else None
        self.staticRows = self._table.get("staticRows", []) or []
        self.parentItemIds = list(self._table.get("parentItemIds", []) or [])
        if not self.parentItemIds and self._table.get("parentItemId") is not None:
            self.parentItemIds = [self._table["parentItemId"]]
        self.parentItemId = self.parentItemIds[0] if self.parentItemIds else None
        self.parentPosition = self._table.get("parentPosition")
        self.breakdownByPosition = bool(
            (table.get("settings") or {}).get("breakdownByPosition", False)
        )
        for bd in table.get("breakdowns", []) or []:
            child = FreeForm(self.title)
            child._is_breakdown = True
            child.columnTree = self.columnTree
            child.raw = deepcopy(bd)
            child._load_table(bd)
            self.breakdowns.append(child)

    @property
    def advancedRows(self) -> list[dict]:
        return (self.raw.get("advancedSettings") or {}).get("rows", []) or []

    @property
    def rows(self) -> int:
        return (self._table.get("pagination") or {}).get("viewBy", 10)

    @property
    def freeformTable(self) -> dict:
        return self._to_freeform_table()

    def _recompute_summaries(self) -> None:
        for child in self.breakdowns:
            child._recompute_summaries()
        table = {
            key: value for key, value in self._table.items() if key != "breakdowns"
        }
        table["staticRows"] = self.staticRows
        metadata = (
            {}
            if self._is_breakdown
            else {
                key: value
                for key, value in self.raw.items()
                if key not in ("columnTree", "freeformTable")
            }
        )
        self._set_components(
            _components(
                {
                    "columnTree": self.columnTree,
                    "table": table,
                    "metadata": metadata,
                }
            )
        )
        self._set_components(
            _merge(self.components, *(bd.components for bd in self.breakdowns))
        )

    def _bind(self, sync: Callable[[], None]) -> None:
        self._sync = sync
        for child in self.breakdowns:
            child._bind(sync)

    def addBreakdown(
        self,
        dimension_id: str = None,
        dimension_name: str = None,
        items: list[dict] = None,
        rows: int = 5,
        parent_item_id: str = None,
    ) -> "FreeForm":
        if bool(dimension_id) == bool(items):
            raise ValueError("Provide either a breakdown dimension or non-empty items.")
        if parent_item_id is None:
            if not self.staticRows:
                raise ValueError(
                    "Dynamic rows require a real parent_item_id from a CJA report."
                )
            parent_item_id = self.staticRows[0]["id"]
        elif self.staticRows and parent_item_id not in {
            row.get("id") for row in self.staticRows
        }:
            raise ValueError("parent_item_id must identify a static row in this table.")
        child = FreeForm(self.title)
        child._is_breakdown = True
        child.columnTree = self.columnTree
        child._load_table(
            _new_freeform_table(
                self.columnTree,
                rows,
                dimension_id,
                dimension_name,
                items,
            )
        )
        child.parentItemId = str(parent_item_id)
        child.parentItemIds = [str(parent_item_id)]
        child._table["parentItemIds"] = child.parentItemIds
        child.raw = deepcopy(child._table)
        child._recompute_summaries()
        if self._sync:
            child._bind(self._sync)
        self.breakdowns.append(child)
        self._recompute_summaries()
        if self._sync:
            self._sync()
        return child

    def _to_freeform_table(self) -> dict:
        table = deepcopy(self._table)
        table["staticRows"] = deepcopy(self.staticRows)
        table["breakdowns"] = [child._to_breakdown_entry() for child in self.breakdowns]
        if self._is_breakdown:
            parent_ids = list(self.parentItemIds)
            if self.parentItemId is not None:
                if parent_ids:
                    parent_ids[0] = self.parentItemId
                else:
                    parent_ids = [self.parentItemId]
            if "parentItemId" in table and "parentItemIds" not in table:
                table["parentItemId"] = self.parentItemId
            elif "parentItemIds" in table or parent_ids:
                table["parentItemIds"] = parent_ids
            table.setdefault("settings", {})["breakdownByPosition"] = (
                self.breakdownByPosition
            )
        return table

    def _to_breakdown_entry(self) -> dict:
        return self._to_freeform_table()

    def to_dict(self) -> dict:
        if self._is_breakdown:
            return self._to_breakdown_entry()
        result = deepcopy(self.raw)
        if "name" in result or self.title:
            result["name"] = self.title
        result["columnTree"] = deepcopy(self.columnTree)
        result["freeformTable"] = self._to_freeform_table()
        return result


FreeformReportlet = FreeForm
_REPORTLET_CLASSES = {
    name: globals()[name]
    for name in __all__
    if name
    not in {
        "WorkspaceManager",
        "WorkspaceDefinition",
        "Panel",
        "TextBuilder",
        "FreeForm",
    }
}


def _column_path(tree: dict, column_id: str) -> list[dict]:
    for node in tree.get("nodes", []) or []:
        if node.get("id") == column_id:
            return [node]
        path = _column_path(node, column_id)
        if path:
            return [node, *path]
    return []


def _selected_components(raw: dict, ff: FreeForm) -> dict[str, list[dict]]:
    selections = [
        node
        for node in _walk(raw.get("lockedSelection", {}))
        if "selectedDataPoints" in node
    ]
    if not selections:
        if raw.get("component"):
            return _components(ff.dimensionSettings or ff.dimension)
        return ff.components
    comps = []
    for selection in selections:
        for point in selection.get("selectedDataPoints", []) or []:
            path = _column_path(ff.columnTree, point.get("columnId"))
            comps.extend(node.get("component", {}) for node in path)
            if path:
                # A selected group column includes all of its descendant columns.
                comps.append(path[-1])
            if point.get("rowItem"):
                comps.append(point["rowItem"])
            pos = point.get("rowPosition")
            if isinstance(pos, int) and 0 <= pos < len(ff.staticRows):
                comps.append(ff.staticRows[pos])
    # Row dimensions and breakdown dimensions supply the visualization's categories.
    comps.append(ff.dimensionSettings or ff.dimension)
    return _components(comps)


class Panel(_ComponentView):
    """A container (SubPanel), table (FreeForm), text, or visualization node."""

    def __init__(self, type_: str, name: str = "", id: str = None):
        self.id = id
        self.name = name
        self.type = type_
        self.raw: dict = {}
        self.position: dict = {}
        self.description = ""
        self.collapsed = False
        self.visible = True
        self.elements: list[Panel] = []
        self.reportlet: Reportlet | None = None
        self.reportletType: str | None = None
        self.freeform: FreeForm | None = None
        self.text: str | None = None
        self.textOps: list[dict] | None = None
        self.chartType: str | None = None
        self.linkedSourceId: str | None = None
        self.linkedSource: Panel | None = None
        self.dateRange: dict | None = None
        self.segmentGroups: list[dict] = []
        self.activeFilters: list[dict] = []
        self.dataViewId: str | None = None
        self.dataViewName: str | None = None
        self.workspaceId: str | None = None
        self.parseWarnings: list[str] = []
        self._set_components(_components({}))

    def _metadata(self, raw: dict) -> None:
        self.raw = deepcopy(raw)
        self.position = self.raw.get("position", {}) or {}
        self.description = self.raw.get("description", "")
        self.collapsed = bool(self.raw.get("collapsed", False))
        self.visible = self.raw.get("visible", True)

    @property
    def rsid(self) -> str | None:
        return self.dataViewId

    @classmethod
    def from_panel_dict(cls, panel: dict) -> "Panel":
        p = cls("SubPanel", panel.get("name", ""), panel.get("id"))
        p._metadata(panel)
        p.dateRange = p.raw.get("dateRange")
        p.segmentGroups = p.raw.get("segmentGroups", []) or []
        dv = panel.get("reportSuite") or panel.get("dataView") or {}
        p.dataViewId = dv.get("id") or panel.get("dataId") or panel.get("rsid")
        p.dataViewName = (dv.get("__metaData__") or {}).get("name", p.dataViewId)
        p.elements = [
            cls.from_subpanel_dict(sp) for sp in panel.get("subPanels", []) or []
        ]
        by_id = {el.id: el for el in p.elements}
        for el in p.elements:
            el.dataViewId, el.dataViewName = p.dataViewId, p.dataViewName
            if el.linkedSourceId:
                el.linkedSource = by_id.get(el.linkedSourceId)
                if el.linkedSource is not None and el.linkedSource.freeform is not None:
                    selected = _selected_components(
                        el.raw.get("reportlet", {}), el.linkedSource.freeform
                    )
                    el._set_components(_merge(el.components, selected))
                    el.reportlet._set_components(el.components)
                elif el.linkedSource is None:
                    el.parseWarnings.append(
                        f"Unresolved linkedSourceId: {el.linkedSourceId}"
                    )
        for group in p.segmentGroups:
            p.activeFilters.extend(
                option["component"]
                for option in group.get("componentOptions", []) or []
                if option.get("isActive") and option.get("component")
            )
            if group.get("dynamicDimension"):
                p.activeFilters.append(group["dynamicDimension"])
        own = {key: value for key, value in panel.items() if key != "subPanels"}
        p._set_components(
            _merge(_components(own), *(el.components for el in p.elements))
        )
        return p

    @classmethod
    def from_subpanel_dict(cls, subpanel: dict) -> "Panel":
        raw = subpanel.get("reportlet", {}) or {}
        reportlet = Reportlet.from_dict(raw)
        ptype = (
            "FreeForm"
            if isinstance(reportlet, FreeForm)
            else ("Text" if isinstance(reportlet, TextReportlet) else "Visualization")
        )
        p = cls(ptype, subpanel.get("name") or raw.get("name", ""), subpanel.get("id"))
        p._metadata(subpanel)
        p.reportlet = reportlet
        p.reportletType = raw.get("type")
        p.linkedSourceId = (
            subpanel.get("linkedSourceId") or raw.get("linkedSourceId") or None
        )
        p._set_components(reportlet.components)
        if isinstance(reportlet, FreeForm):
            p.freeform = reportlet
        elif isinstance(reportlet, TextReportlet):
            p.text, p.textOps = reportlet.text, reportlet.textOps
            p.parseWarnings.extend(reportlet.parseWarnings)
        else:
            p.chartType = p.reportletType
        return p

    def to_dict(self) -> dict:
        return deepcopy(self.raw)

    def _summary_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "reportletType": self.reportletType,
            "dataViewId": self.dataViewId,
            "position": self.position,
            **self.components,
            "elements": [el._summary_dict() for el in self.elements],
            "text": self.text,
            "linkedSourceId": self.linkedSourceId,
        }

    def __str__(self) -> str:
        return json.dumps(self._summary_dict(), indent=2)

    __repr__ = __str__


class WorkspaceDefinition(_ComponentView):
    """One workspace in a project; distinct from the getReport Workspace class."""

    def __init__(self, raw: dict):
        self.raw = deepcopy(raw)
        self.id = raw.get("id")
        self.name = raw.get("name", "")
        self.panels = [
            Panel.from_panel_dict(panel) for panel in raw.get("panels", []) or []
        ]
        for panel in self.panels:
            panel.workspaceId = self.id
            for element in panel.elements:
                element.workspaceId = self.id
        own = {key: value for key, value in raw.items() if key != "panels"}
        self._set_components(
            _merge(_components(own), *(p.components for p in self.panels))
        )

    def to_dict(self) -> dict:
        return deepcopy(self.raw)


class WorkspaceManager(_ComponentView):
    """Read/edit projects offline or build them with an optional CJA connection.

    All aanalytics2 public builder methods are available. ``dataViewId`` replaces
    ``rsid`` conceptually; ``rsid`` and ``analytics`` remain compatibility aliases.
    API lookups are lazy, cached, and always use the CJA client's transport.
    """

    DEFAULT_COLOR_SCHEME = _COLORS

    def __init__(
        self,
        data: dict | str | Path = None,
        rsid: str = None,
        name: str = None,
        description: str = None,
        tags: list[int | dict] = None,
        shares: list[dict] = None,
        config=None,
        companyId=None,
        analytics=None,
        *,
        dataViewId: str = None,
        cja=None,
        project_details: dict = None,
    ) -> None:
        if data is not None and project_details is not None:
            raise ValueError("Use data or project_details, not both.")
        data = project_details if project_details is not None else data
        if rsid and dataViewId and rsid != dataViewId:
            raise ValueError("rsid and dataViewId must refer to the same data view.")
        if cja is not None and analytics is not None and cja is not analytics:
            raise ValueError("Use cja or analytics, not different connections.")
        self._cja = cja if cja is not None else analytics
        if self._cja is None and config is not None:
            from .cjapy import CJA

            self._cja = CJA(config_object=config)
        self._analytics = self._cja
        self._config = config
        self._catalogs: dict[tuple[str, str], dict[str, str]] = {}
        self._current_workspace_index = 0
        self._current_panel_index = -1
        self._layout: dict[str, tuple[int, int]] = {}
        self._live_freeforms: dict[str, FreeForm] = {}
        if isinstance(data, Path) or (
            isinstance(data, str) and not data.lstrip().startswith(("{", "["))
        ):
            with Path(data).open(encoding="utf-8-sig") as stream:
                data = json.load(stream)
        elif isinstance(data, str):
            data = json.loads(data)
        if data is not None and not isinstance(data, dict):
            raise TypeError(
                "data must be a project dictionary, JSON string, or file path."
            )
        if data is None:
            if not (dataViewId or rsid) or not name:
                raise ValueError(
                    "dataViewId and name are required when building a new project."
                )
            self._project = {
                "name": name,
                "description": description or "",
                "dataId": dataViewId or rsid,
                "type": "project",
                "definition": {
                    "additionalCuratedComponents": [],
                    "colorScheme": {
                        "id": "default",
                        "label": "",
                        "value": list(_COLORS),
                    },
                    "countRepeatInstances": True,
                    "currentWorkspaceIndex": 0,
                    "customColorSchemes": [],
                    "hideCommentRail": False,
                    "internalAnnotations": [],
                    "intrinsicPublicAccessLinkComponents": [],
                    "isCurated": False,
                    "showAnnotations": True,
                    "version": "110",
                    "viewDensity": "expanded",
                    "workspaces": [{"id": _uuid(), "name": name, "panels": []}],
                },
            }
        else:
            self._project = deepcopy(
                data if "definition" in data else {"definition": data}
            )
        self.id = self._project.get("id")
        self.name = name if name is not None else self._project.get("name", "")
        self.description = (
            description
            if description is not None
            else self._project.get("description", "")
        )
        self.dataViewId = (
            dataViewId
            or rsid
            or self._project.get("dataId")
            or self._project.get("rsid", "")
        )
        if not self.dataViewId:
            for node in _walk(self._project.get("definition", {})):
                if node.get("type") == "ReportSuite" and node.get("id"):
                    self.dataViewId = node["id"]
                    break
        self.dataViewName = self._project.get("dataViewName", self.dataViewId)
        self.owner = deepcopy(self._project.get("owner"))
        self.tags = deepcopy(self._project.get("tags", []))
        self.shares = deepcopy(self._project.get("shares", []))
        self.created = self._project.get("created", "")
        self.modified = self._project.get("modified", "")
        self.version = self.definition.get("version", "")
        for field in ("approved", "companyTemplate", "organizationTemplate"):
            setattr(self, field, self._project.get(field))
        for tag in tags or []:
            self.addTag(tag)
        self.shares.extend(deepcopy(shares or []))
        workspaces = self.definition.get("workspaces", []) or []
        if workspaces:
            index = self.definition.get("currentWorkspaceIndex", 0)
            self._current_workspace_index = (
                index if isinstance(index, int) and 0 <= index < len(workspaces) else 0
            )
            self._current_panel_index = len(self._panels) - 1
        if dataViewId or rsid:
            self.replaceDataView(self.dataViewId, self.dataViewName)

    @property
    def rsid(self) -> str:
        return self.dataViewId

    @rsid.setter
    def rsid(self, value: str) -> None:
        self.dataViewId = value

    @property
    def rsid_name(self) -> str:
        return self.dataViewName

    @property
    def project_id(self) -> str | None:
        return self.id

    @property
    def project_details(self) -> dict:
        return self.to_dict()

    @property
    def definition(self) -> dict:
        return self._project.setdefault("definition", {})

    @property
    def _panels(self) -> list[dict]:
        workspaces = self.definition.get("workspaces", []) or []
        if not workspaces:
            return []
        return workspaces[self._current_workspace_index].setdefault("panels", [])

    @property
    def workspaces(self) -> list[WorkspaceDefinition]:
        return [
            WorkspaceDefinition(ws)
            for ws in self.definition.get("workspaces", []) or []
        ]

    @property
    def panels(self) -> list[Panel]:
        return [panel for workspace in self.workspaces for panel in workspace.panels]

    @property
    def components(self) -> dict[str, list[dict]]:
        # Include curated components, mobile scorecards, and guided analyses too.
        summary = _components(self.definition)
        if self._project.get("type") == "guidedAnalysis":
            groups = self.definition.get("peopleSegments", []) or []
            legacy = [
                _component(group["id"], group.get("name", group["id"]), "Segment")
                for group in groups
                if group.get("id") and not group.get("segmentId")
            ]
            summary = _merge(summary, _components(legacy))
        if self.dataViewId and not summary["dataViews"]:
            summary["dataViews"] = [{"id": self.dataViewId, "name": self.dataViewName}]
        return summary

    @property
    def dimensions(self) -> list[dict]:
        return self.components["dimensions"]

    @property
    def dimensionItems(self) -> list[dict]:
        return self.components["dimensionItems"]

    @property
    def metrics(self) -> list[dict]:
        return self.components["metrics"]

    @property
    def calculatedMetrics(self) -> list[dict]:
        return self.components["calculatedMetrics"]

    @property
    def segments(self) -> list[dict]:
        return self.components["segments"]

    @property
    def dateRanges(self) -> list[dict]:
        return self.components["dateRanges"]

    @property
    def dataViews(self) -> list[dict]:
        return self.components["dataViews"]

    @property
    def annotations(self) -> list[dict]:
        return self.components["annotations"]

    @property
    def attributionTemplates(self) -> list[dict]:
        return self.components["attributionTemplates"]

    @property
    def nbPanels(self) -> int:
        return sum(
            len(ws.get("panels", []))
            for ws in self.definition.get("workspaces", []) or []
        )

    @property
    def nbSubPanels(self) -> int:
        return sum(
            len(p.get("subPanels", []))
            for ws in self.definition.get("workspaces", []) or []
            for p in ws.get("panels", [])
        )

    def addWorkspace(self, name: str = "") -> "WorkspaceManager":
        if self._project.get("type", "project") != "project":
            raise ValueError("Workspace builders require a desktop project.")
        workspaces = self.definition.setdefault("workspaces", [])
        workspaces.append({"id": _uuid(), "name": name, "panels": []})
        return self.selectWorkspace(len(workspaces) - 1)

    def selectWorkspace(self, workspace: int | str) -> "WorkspaceManager":
        workspaces = self.definition.get("workspaces", []) or []
        self._current_workspace_index = self._select_index(
            workspaces, workspace, "workspace"
        )
        self._current_panel_index = len(self._panels) - 1
        return self

    @staticmethod
    def _select_index(items: list[dict], selector: int | str, label: str) -> int:
        if isinstance(selector, int):
            if not 0 <= selector < len(items):
                raise IndexError(f"{label} index {selector} is out of range.")
            return selector
        matches = [
            i
            for i, item in enumerate(items)
            if selector in (item.get("id"), item.get("name"))
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one {label} matching {selector!r}, found {len(matches)}."
            )
        return matches[0]

    def selectPanel(self, panel: int | str) -> "WorkspaceManager":
        self._current_panel_index = self._select_index(self._panels, panel, "panel")
        return self

    def _current_panel(self) -> dict:
        if self._current_panel_index < 0 or not self._panels:
            raise ValueError("No panel selected. Call addPanel() first.")
        return self._panels[self._current_panel_index]

    def _catalog(self, kind: str) -> dict[str, str]:
        dv = (
            self._panel_data_id()
            if kind in ("dimensions", "metrics", "calculatedMetrics", "segments")
            else ""
        )
        key = (kind, dv)
        scoped = {
            field: value
            for field, value in self.definition.items()
            if field != "workspaces"
        }
        panels = [
            panel
            for ws in self.definition.get("workspaces", []) or []
            for panel in ws.get("panels", []) or []
            if not dv
            or (
                (panel.get("reportSuite") or {}).get("id")
                or panel.get("dataId")
                or panel.get("rsid")
                or self.dataViewId
            )
            == dv
        ]
        names = {
            comp["id"]: comp["name"] for comp in _components([scoped, panels])[kind]
        }
        if key not in self._catalogs:
            fetched = {}
            if self._cja is not None:
                if kind == "dimensions":
                    data = self._cja.getDimensions(dataviewId=dv, output="raw")
                elif kind == "metrics":
                    data = self._cja.getMetrics(dataviewId=dv, output="raw")
                elif kind == "segments":
                    data = self._cja.getFilters(dataIds=dv, output="raw")
                elif kind == "calculatedMetrics":
                    data = self._cja.getCalculatedMetrics(dataIds=dv, output="raw")
                else:
                    data = self._cja.getDateRanges(output="raw")
                if not isinstance(data, list):
                    raise TypeError(f"CJA {kind} lookup did not return a list.")
                fetched = {el["id"]: el["name"] for el in data}
            self._catalogs[key] = fetched
        return {**names, **self._catalogs[key]}

    def _panel_data_id(self) -> str:
        if self._current_panel_index >= 0 and self._panels:
            panel = self._current_panel()
            return (
                (panel.get("reportSuite") or {}).get("id")
                or panel.get("dataId")
                or panel.get("rsid")
                or self.dataViewId
            )
        return self.dataViewId

    def _resolve_pair(self, kind: str, id_: str, name: str) -> tuple[str, str]:
        if not id_ and not name:
            raise ValueError(f"A {kind} ID or name is required.")
        if id_ and name:
            return id_, name
        names = self._catalog(kind)
        if id_:
            return id_, names.get(id_, id_)
        matches = [
            cid for cid, label in names.items() if label.casefold() == name.casefold()
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one {kind} named {name!r}, found {len(matches)}. Provide an ID."
            )
        return matches[0], name

    def _resolve_metric_pair(self, mid: str, mname: str) -> tuple[str, str]:
        if mid:
            return self._resolve_pair(
                "calculatedMetrics" if mid.startswith("cm") else "metrics", mid, mname
            )
        matches = [
            cid
            for kind in ("metrics", "calculatedMetrics")
            for cid, label in self._catalog(kind).items()
            if label.casefold() == (mname or "").casefold()
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one metric named {mname!r}, found {len(matches)}. Provide an ID."
            )
        return matches[0], mname

    def _resolve_dim_pair(self, did: str, dname: str) -> tuple[str, str]:
        return self._resolve_pair("dimensions", did, dname)

    def _resolve_seg_pair(self, sid: str, sname: str) -> tuple[str, str]:
        return self._resolve_pair("segments", sid, sname)

    def _normalize_metrics(self, metrics: list[dict]) -> list[dict]:
        result = []
        for metric in metrics:
            mid, name = self._resolve_metric_pair(metric.get("id"), metric.get("name"))
            filters = self._normalize_items(metric.get("filters", []))
            result.append(
                {
                    **metric,
                    "id": mid,
                    "name": name,
                    **({"filters": filters} if filters else {}),
                }
            )
        return result

    def _normalize_items(self, items: list[dict]) -> list[dict]:
        result = []
        for item in items:
            cid, name = item.get("id"), item.get("name")
            type_ = item.get("type") or (_detect_component_type(cid) if cid else None)
            if type_ == "DimensionItem" and cid:
                name = name or cid.split("::", 1)[1]
            else:
                kind = _COMPONENT_TYPES.get(type_ or "Dimension")
                if kind is None:
                    raise ValueError(f"Unsupported component type: {type_}")
                if cid or type_:
                    cid, name = self._resolve_pair(kind, cid, name)
                else:
                    matches = [
                        (cid_, label, component_type)
                        for component_type, category in (
                            ("Dimension", "dimensions"),
                            ("Segment", "segments"),
                        )
                        for cid_, label in self._catalog(category).items()
                        if label.casefold() == (name or "").casefold()
                    ]
                    if len(matches) != 1:
                        raise ValueError(
                            f"Expected one component named {name!r}, found {len(matches)}."
                        )
                    cid, name, type_ = matches[0]
            result.append(
                {
                    **item,
                    "id": cid,
                    "name": name,
                    "type": type_ or _detect_component_type(cid),
                }
            )
        return result

    def addPanel(
        self,
        name: str,
        date_range: str = "thisMonth",
        position: int = None,
        collapsed: bool = False,
        description: str = "",
        *,
        dataViewId: str = None,
        dataViewName: str = None,
    ) -> "WorkspaceManager":
        if self._project.get("type", "project") != "project":
            raise ValueError("Workspace builders require a desktop project.")
        if "/" in date_range:
            start, end = date_range.split("/", 1)
            if datetime.fromisoformat(
                start.replace("Z", "+00:00")
            ) >= datetime.fromisoformat(end.replace("Z", "+00:00")):
                raise ValueError("The date interval must end after it starts.")
            date = {
                "__entity__": True,
                "type": "DateRange",
                "__metaData__": {"definition": date_range},
            }
        else:
            presets = {
                "thisMonth": "This Month",
                "lastFullMonth": "Last Month",
                "thisWeek": "This Week",
                "lastFullWeek": "Last Week",
                "today": "Today",
                "yesterday": "Yesterday",
            }
            did, label = (
                (date_range, presets[date_range])
                if date_range in presets
                else self._resolve_pair("dateRanges", date_range, None)
            )
            date = _component(did, label, "DateRange")
        dv = dataViewId or self.dataViewId
        if not dv:
            raise ValueError("A dataViewId is required to add a panel.")
        dv_name = dataViewName or self.dataViewName or dv
        panel = {
            "collapsed": collapsed,
            "dateRange": date,
            "datesAreRelativeToPanel": False,
            "description": description,
            "id": _uuid(),
            "name": name,
            "position": {
                "autoHeight": 0,
                "autoSize": True,
                "width": 100,
                "x": 0,
                "y": 0,
            },
            "reportSuite": _component(dv, dv_name, "ReportSuite"),
            "segmentGroups": [],
            "subPanels": [],
            "type": "panel",
        }
        panel["reportSuite"]["__metaData__"]["rsid"] = dv
        if not self.definition.get("workspaces"):
            self.addWorkspace(self.name)
        index = (
            len(self._panels)
            if position is None
            else max(0, min(position, len(self._panels)))
        )
        self._panels.insert(index, panel)
        self._current_panel_index = index
        return self

    def _append(
        self,
        title: str,
        reportlet: dict,
        height: int,
        collapsed: bool = False,
        description: str = "",
    ) -> dict:
        panel = self._current_panel()
        subs = panel.setdefault("subPanels", [])
        if panel["id"] not in self._layout:
            y = max(
                (
                    sp.get("position", {}).get("y", 0)
                    + sp.get("position", {}).get("autoHeight", 0)
                    for sp in subs
                ),
                default=0,
            )
            viz = max((sp.get("visualizationIndex", 0) for sp in subs), default=0) + 1
            self._layout[panel["id"]] = (y, viz)
        y, viz = self._layout[panel["id"]]
        sub = {
            "collapsed": collapsed,
            "description": description,
            "id": _uuid(),
            "isQuickInsightsSubPanel": False,
            "linkedSourceId": "",
            "name": title,
            "position": {
                "autoHeight": height,
                "autoSize": True,
                "width": 100,
                "x": 0,
                "y": y,
            },
            "reportlet": reportlet,
            "swatchColor": _COLORS[len(subs) % 12],
            "type": "genericSubPanel",
            "visible": True,
            "visualizationIndex": viz,
        }
        subs.append(sub)
        self._layout[panel["id"]] = (y + height, viz + 1)
        panel.setdefault("position", {})["autoHeight"] = y + height
        return sub

    def addTextFreeform(
        self,
        title: str,
        content: str | TextBuilder | dict,
        collapsed: bool = False,
        description: str = "",
    ) -> "WorkspaceManager":
        if hasattr(content, "to_dict") and not isinstance(content, dict):
            content = content.to_dict()
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = None
            content = (
                parsed
                if isinstance(parsed, dict) and "ops" in parsed
                else {"ops": [{"insert": content + "\n"}]}
            )
        if not isinstance(content, dict) or not isinstance(content.get("ops"), list):
            raise ValueError(
                "Text content must be plain text, a TextBuilder, or a Quill Delta object."
            )
        self._append(
            title,
            {
                "disabled": False,
                "hideTitle": False,
                "isConfigVisible": True,
                "name": title,
                "readOnly": False,
                "showAnnotations": True,
                "showControls": True,
                "showVizSelectorOnSubPanel": False,
                "textContent": json.dumps(content),
                "type": "TextReportlet",
                "useRowBasedPercentages": False,
            },
            321,
            collapsed,
            description,
        )
        return self

    def addFreeform(
        self,
        title: str,
        item_id: str = None,
        item_name: str = "",
        items: list[dict] = None,
        metrics: list[dict] = None,
        rows: int = 10,
        collapsed: bool = False,
        description: str = "",
    ) -> FreeForm:
        self._current_panel()
        if not metrics:
            raise ValueError("At least one metric is required.")
        if items is not None and (item_id or item_name):
            raise ValueError("Use items or item_id/item_name, not both.")
        dim_id = dim_name = None
        if items is None:
            item = self._normalize_items([{"id": item_id, "name": item_name}])[0]
            if item["type"] == "Dimension":
                dim_id, dim_name = item["id"], item["name"]
            else:
                items = [item]
        else:
            items = self._normalize_items(items)
        ff = FreeForm.build(
            title, self._normalize_metrics(metrics), dim_id, dim_name, items, rows
        )
        sub = self._append(title, ff.to_dict(), 528, collapsed, description)

        def sync() -> None:
            ff._recompute_summaries()
            sub["reportlet"] = ff.to_dict()

        ff._bind(sync)
        self._live_freeforms[sub["id"]] = ff
        return ff

    def addSegmentFilter(self, segment: str = None) -> "WorkspaceManager":
        if not segment:
            raise ValueError("A filter ID or name is required.")
        names = self._catalog("segments")
        is_name = any(
            label.casefold() == segment.casefold() for label in names.values()
        )
        is_id = segment in names or not is_name
        sid, label = self._resolve_seg_pair(
            segment if is_id else None, None if is_id else segment
        )
        self.addDropdownFilter(
            "", [{"id": sid, "name": label, "type": "Segment"}], False
        )
        self._current_panel()["segmentGroups"][-1]["runAs"] = "segment"
        return self

    def addFilter(self, filter_id: str = None, name: str = None) -> "WorkspaceManager":
        cid, label = self._resolve_seg_pair(filter_id, name)
        return self.addDropdownFilter(
            "", [{"id": cid, "name": label, "type": "Segment"}], False
        )

    def addDropdownFilter(
        self,
        group_name: str,
        components: list[dict],
        has_no_filter: bool = True,
    ) -> "WorkspaceManager":
        if not components:
            raise ValueError("At least one dropdown option is required.")
        options = self._normalize_items(components)
        explicit_active = any("isActive" in option for option in options)
        options = [
            {
                "component": _component(item["id"], item["name"], item["type"]),
                "isActive": bool(item.get("isActive", not explicit_active and i == 0)),
            }
            for i, item in enumerate(options)
        ]
        active = sum(option["isActive"] for option in options)
        if active > 1 or (not has_no_filter and active != 1):
            raise ValueError(
                "Dropdown groups require at most one active option, or exactly one without No filter."
            )
        self._current_panel().setdefault("segmentGroups", []).append(
            {
                "componentOptions": options,
                "groupName": group_name,
                "hasNoFilter": has_no_filter,
                "showGroupName": True,
            }
        )
        return self

    def addActivityBreakdownFreeform(
        self,
        title: str,
        activity_dim_item_id: str,
        activity_name: str,
        breakdown_dim_id: str,
        breakdown_dim_name: str,
        metrics: list[dict],
        rows: int = 50,
        breakdown_rows: int = 5,
        collapsed: bool = False,
        description: str = "",
    ) -> "WorkspaceManager":
        did, label = self._resolve_dim_pair(breakdown_dim_id, breakdown_dim_name)
        ff = self.addFreeform(
            title,
            items=[
                {
                    "id": activity_dim_item_id.replace(":::", "::"),
                    "name": activity_name,
                    "type": "DimensionItem",
                }
            ],
            metrics=metrics,
            rows=rows,
            collapsed=collapsed,
            description=description,
        )
        ff.addBreakdown(did, label, rows=breakdown_rows)
        return self

    def addSegmentAsDimensionFreeform(
        self,
        title: str,
        segments: list[dict],
        metrics: list[dict],
        breakdown_dim_id: str = None,
        breakdown_dim_name: str = "",
        breakdown_segments: list[dict] = None,
        breakdown_rows: int = 5,
        rows: int = 50,
        collapsed: bool = False,
        description: str = "",
    ) -> "WorkspaceManager":
        if breakdown_segments is not None and (breakdown_dim_id or breakdown_dim_name):
            raise ValueError(
                "Choose dimension breakdowns or segment breakdowns, not both."
            )
        items = [{**segment, "type": "Segment"} for segment in segments]
        did = label = None
        if breakdown_dim_id or breakdown_dim_name:
            did, label = self._resolve_dim_pair(breakdown_dim_id, breakdown_dim_name)
        breakdown_items = (
            self._normalize_items(
                [{**segment, "type": "Segment"} for segment in breakdown_segments]
            )
            if breakdown_segments
            else None
        )
        ff = self.addFreeform(
            title,
            items=items,
            metrics=metrics,
            rows=rows,
            collapsed=collapsed,
            description=description,
        )
        if did or breakdown_items:
            for row in ff.staticRows:
                ff.addBreakdown(did, label, breakdown_items, breakdown_rows, row["id"])
        return self

    def _freeform_sources(self, source: str | int = None) -> list[dict]:
        subs = self._current_panel().get("subPanels", [])
        if source == "all":
            selected = [
                sub
                for sub in subs
                if sub.get("reportlet", {}).get("type") == "FreeformReportlet"
            ]
        elif source is None:
            selected = next(
                (
                    [sub]
                    for sub in reversed(subs)
                    if sub.get("reportlet", {}).get("type") == "FreeformReportlet"
                ),
                [],
            )
        else:
            selected = [subs[self._select_index(subs, source, "sub-panel")]]
        if not selected or any(
            sub.get("reportlet", {}).get("type") != "FreeformReportlet"
            for sub in selected
        ):
            raise ValueError("The source must be an existing FreeformReportlet.")
        return selected

    def getFreeform(self, source: str | int = None) -> FreeForm:
        """Return a live editable table in the selected panel, including loaded tables."""
        sub = self._freeform_sources(source)[0]
        if sub["id"] not in self._live_freeforms:
            ff = FreeForm.from_dict(sub["reportlet"])

            def sync() -> None:
                ff._recompute_summaries()
                sub["reportlet"] = ff.to_dict()

            ff._bind(sync)
            self._live_freeforms[sub["id"]] = ff
        return self._live_freeforms[sub["id"]]

    def addChart(
        self,
        viz_type: str,
        source: str | int = None,
        title: str = "",
        collapsed: bool = False,
        description: str = "",
    ) -> "WorkspaceManager":
        type_ = _VIZ_TYPE_MAP.get(viz_type.lower())
        if type_ is None:
            raise ValueError(
                f"Unknown chart type {viz_type!r}. Supported: {list(_VIZ_TYPE_MAP)}"
            )
        backing = self._freeform_sources(source)[0]
        sub = self._append(
            title,
            {
                "hideTitle": False,
                "name": title,
                "showAnnotations": True,
                "showControls": True,
                "type": type_,
            },
            300,
            collapsed,
            description,
        )
        sub["linkedSourceId"] = backing["id"]
        return self

    def addSummaryNumber(
        self,
        title: str,
        metric: str = None,
        show_change: bool = False,
        show_percent_change: bool = False,
        show_sparkline: bool = False,
        collapsed: bool = False,
        description: str = "",
    ) -> "WorkspaceManager":
        if show_change or show_percent_change or show_sparkline:
            raise NotImplementedError(
                "Summary-number change/sparkline flags are not supported by this reportlet."
            )
        if not metric:
            raise ValueError("A metric ID or name is required.")
        kind = _detect_component_type(metric)
        is_id = kind in ("Metric", "CalculatedMetric") or metric.startswith("_")
        if not is_id:
            is_id = metric in self._catalog("metrics") or metric in self._catalog(
                "calculatedMetrics"
            )
        mid, label = self._resolve_metric_pair(
            metric if is_id else None,
            None if is_id else metric,
        )
        # A segment row provides the grand total without an Analytics-only dimension.
        ff = FreeForm.build(
            f"{title} (data)",
            [{"id": mid, "name": label}],
            items=[
                {"id": "All_Visits", "name": "All Events", "type": "Segment"},
            ],
        )
        summary = self._append(
            title,
            {
                "abbreviatePrecision": 0,
                "abbreviateValue": False,
                "isConfigVisible": True,
                "legendVisible": False,
                "lockedSelection": {
                    "breakdowns": [],
                    "selectedDataPoints": [
                        {
                            "columnId": ff.columnTree["nodes"][0]["id"],
                            "rowPosition": -1,
                        }
                    ],
                    "type": "FreeformBreakdownSelection",
                },
                "lockType": "positions",
                "name": title,
                "showVizSelectorOnSubPanel": False,
                "sourceCoords": "",
                "summarizeValue": False,
                "summarizeValueBy": "max",
                "type": "SummaryNumberReportlet",
                "usePercentage": False,
                "useRowBasedPercentages": False,
            },
            200,
            collapsed,
            description,
        )
        backing = self._append(f"{title} (data)", ff.to_dict(), 300)
        summary["linkedSourceId"] = backing["id"]
        return self

    def addBreakdownToDimension(
        self,
        breakdown_dim_id: str = None,
        breakdown_dim_name: str = None,
        target: str | int = "all",
        breakdown_rows: int = 5,
        *,
        parent_item_id: str = None,
    ) -> "WorkspaceManager":
        did, label = self._resolve_dim_pair(breakdown_dim_id, breakdown_dim_name)
        candidates = self._freeform_sources(target)
        changes = []
        for sub in candidates:
            ff = FreeForm.from_dict(sub["reportlet"])
            if ff.staticRows and parent_item_id is None:
                for row in ff.staticRows:
                    ff.addBreakdown(
                        did, label, rows=breakdown_rows, parent_item_id=row["id"]
                    )
            else:
                ff.addBreakdown(
                    did, label, rows=breakdown_rows, parent_item_id=parent_item_id
                )
            changes.append((sub, ff))
        for sub, staged in changes:
            live = self._live_freeforms.get(sub["id"])
            if live is None:
                sub["reportlet"] = staged.to_dict()
            else:
                sync = live._sync
                if sync is None:
                    raise RuntimeError(
                        "The editable table has lost its project binding."
                    )
                additions = staged.breakdowns[len(live.breakdowns) :]
                for child in additions:
                    child._bind(sync)
                    live.breakdowns.append(child)
                live._recompute_summaries()
                sync()
        return self

    def replaceDataView(
        self,
        dataViewId: str,
        name: str = None,
        oldDataViewId: str = None,
    ) -> "WorkspaceManager":
        """Replace data-view references, not dimension/metric/filter identities."""
        if not dataViewId:
            raise ValueError("A dataViewId is required.")
        if oldDataViewId is None or self.dataViewId == oldDataViewId:
            self.dataViewId, self.dataViewName = dataViewId, name or dataViewId
            self._project["dataId"] = dataViewId
            if "rsid" in self._project:
                self._project["rsid"] = dataViewId
        for node in _walk(self.definition):
            if node.get("type") in ("ReportSuite", "DataView") and (
                oldDataViewId is None or node.get("id") == oldDataViewId
            ):
                node["id"] = dataViewId
                meta = node.setdefault("__metaData__", {})
                meta["rsid"] = dataViewId
                if name is not None:
                    meta["name"] = name
            for field in ("rsid", "dataId"):
                if field in node and (
                    oldDataViewId is None or node[field] == oldDataViewId
                ):
                    node[field] = dataViewId
        self._catalogs.clear()
        return self

    def setOwner(self, owner: int | str | dict) -> "WorkspaceManager":
        self.owner = (
            deepcopy(owner)
            if isinstance(owner, dict)
            else ({"imsUserId": owner} if isinstance(owner, str) else {"id": owner})
        )
        return self

    def addTag(self, tag: int | dict) -> "WorkspaceManager":
        value = {"id": tag} if isinstance(tag, int) else deepcopy(tag)
        if "id" not in value:
            raise ValueError("Tags require an id.")
        if not any(existing.get("id") == value["id"] for existing in self.tags):
            self.tags.append(value)
        return self

    def addShare(
        self,
        share_to_id: int | str = None,
        share_to_type: str = "user",
        share_to_display_name: str = None,
    ) -> "WorkspaceManager":
        if share_to_type not in ("user", "group", "all") or (
            share_to_type != "all" and share_to_id is None
        ):
            raise ValueError("Shares require user/group plus an ID, or type all.")
        share = {"shareToType": share_to_type}
        if share_to_id is not None:
            share["shareToId"] = share_to_id
        if share_to_display_name is not None:
            share["shareToDisplayName"] = share_to_display_name
        self.shares.append(share)
        return self

    def to_dict(self) -> dict:
        """Return a detached, lossless project dictionary, including unknown fields."""
        result = deepcopy(self._project)
        for field in ("name", "description"):
            value = getattr(self, field)
            if field in result or value:
                result[field] = value
        if self.id is not None:
            result["id"] = self.id
        for field in ("owner", "approved", "companyTemplate", "organizationTemplate"):
            value = getattr(self, field)
            if value is not None:
                result[field] = deepcopy(value)
        for field in ("tags", "shares"):
            value = getattr(self, field)
            if value or field in result:
                result[field] = deepcopy(value)
        return result

    def to_json(self, filename: str | Path = None) -> str:
        content = json.dumps(self.to_dict(), indent=2)
        if filename is not None:
            Path(filename).write_text(content, encoding="utf-8")
        return content

    def _connection(self):
        if self._cja is None:
            raise ValueError("A CJA connection is required for API operations.")
        return self._cja

    def _api_payload(self) -> dict:
        result = self.to_dict()
        # GET expansions are not writable project fields. Keep them in to_dict(),
        # but do not send them back to Adobe's create/update endpoints.
        writable = {
            "name",
            "description",
            "dataId",
            "owner",
            "type",
            "definition",
            "approved",
            "companyTemplate",
            "organizationTemplate",
        }
        result = {key: value for key, value in result.items() if key in writable}
        if self.dataViewId:
            result["dataId"] = self.dataViewId
        if self.owner:
            if self.owner.get("imsUserId"):
                result["owner"] = {"imsUserId": self.owner["imsUserId"]}
            elif self.owner.get("id") is not None:
                result["owner"] = {"id": self.owner["id"]}
            else:
                raise ValueError(
                    "The owner must have an imsUserId or id for API operations."
                )
        if self.tags or self.shares:
            warnings.warn(
                "The Projects API does not write tags/shares through project bodies; "
                "these local fields are excluded from the API payload.",
                UserWarning,
                stacklevel=3,
            )
        return result

    def createProject(self) -> dict:
        if self.id is not None:
            raise ValueError(
                "This project already has an ID. Use updateProject(), or duplicate with an ID-free definition."
            )
        response = self._connection().createProject(self._api_payload())
        if not isinstance(response, dict) or not response.get("id"):
            raise ValueError(f"CJA did not return a created project ID: {response!r}")
        self.id = response["id"]
        return response

    def updateProject(self) -> dict:
        if self.id is None:
            raise ValueError(
                "A persisted project ID is required. Load a project or call createProject() first."
            )
        return self._connection().updateProject(self.id, self._api_payload())

    def validateProject(self) -> dict:
        return self._connection().validateProject(self._api_payload())

    def __str__(self) -> str:
        return self.to_json()

    __repr__ = __str__
