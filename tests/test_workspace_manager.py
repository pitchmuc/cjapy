"""Synthetic workspace fixtures: customer exports never become test assets."""

import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

import pytest

import cjapy
from cjapy.workspaceManager import (
    BarStackedReportlet,
    FreeForm,
    LineReportlet,
    Reportlet,
    TextBuilder,
    TextReportlet,
    WorkspaceManager,
)


def component(id_, type_, name=None):
    return {
        "id": id_,
        "type": type_,
        "__entity__": True,
        "__metaData__": {"name": name or id_},
    }


def project_fixture():
    table = FreeForm.build(
        "Traffic",
        [
            {
                "id": "metrics/events",
                "name": "Events",
                "filters": [
                    {"id": "s-column", "name": "Column filter"},
                ],
            }
        ],
        dim_id="variables/page",
        dim_name="Page",
    ).to_dict()
    table["freeformTable"]["dimensionSettings"].append(
        {
            "id": "dim-second",
            "dimension": component("variables/device", "Dimension"),
            "search": {"rules": []},
        }
    )
    table["freeformTable"]["breakdowns"] = [
        {
            "dimension": component("variables/channel", "Dimension"),
            "staticRows": [],
            "breakdowns": [
                {
                    "dimensions": [component("variables/country", "Dimension")],
                    "staticRows": [
                        {"id": "row", "component": component("s-deep", "Segment")}
                    ],
                    "breakdowns": [],
                    "parentItemIds": ["a", "b"],
                    "settings": {"breakdownByPosition": False},
                }
            ],
            "parentItemId": "42",
            "settings": {"breakdownByPosition": False},
        }
    ]
    column = table["columnTree"]["nodes"][0]
    metric_id = column["nodes"][0]["id"]
    return {
        "id": "project-id",
        "name": "Example",
        "type": "project",
        "dataId": "dv-one",
        "description": "",
        "created": "2026-01-01",
        "modified": "2026-02-01",
        "approved": False,
        "organizationTemplate": False,
        "owner": {"imsUserId": "user-id", "name": "Owner", "login": "owner"},
        "tags": [{"id": 1}],
        "shares": [],
        "futureRootField": {"keep": True},
        "definition": {
            "version": "110",
            "futureDefinitionField": [1, 2],
            "additionalCuratedComponents": [
                component("cm-curated", "CalculatedMetric")
            ],
            "workspaces": [
                {
                    "id": "workspace-one",
                    "name": "First",
                    "panels": [
                        {
                            "id": "panel-one",
                            "name": "Overview",
                            "type": "panel",
                            "position": {"y": 5, "autoHeight": 987},
                            "reportSuite": component("dv-one", "ReportSuite"),
                            "dateRange": component("thisMonth", "DateRange"),
                            "segmentGroups": [
                                {
                                    "componentOptions": [
                                        {
                                            "component": component(
                                                "s-active", "Segment"
                                            ),
                                            "isActive": True,
                                        },
                                        {
                                            "component": component(
                                                "s-inactive", "Segment"
                                            ),
                                            "isActive": False,
                                        },
                                    ],
                                    "dynamicDimension": component(
                                        "variables/filter", "Dimension"
                                    ),
                                }
                            ],
                            "subPanels": [
                                {"id": "table", "name": "Traffic", "reportlet": table},
                                {
                                    "id": "chart",
                                    "name": "Trend",
                                    "linkedSourceId": "table",
                                    "reportlet": {
                                        "type": "LineReportlet",
                                        "lockedSelection": {
                                            "selectedDataPoints": [
                                                {
                                                    "columnId": metric_id,
                                                    "rowPosition": -1,
                                                }
                                            ],
                                        },
                                    },
                                },
                                {
                                    "id": "flow",
                                    "reportlet": {
                                        "type": "Flow",
                                        "rootComponent": component(
                                            "variables/flow", "Dimension"
                                        ),
                                    },
                                },
                            ],
                        }
                    ],
                },
                {
                    "id": "workspace-two",
                    "name": "Second",
                    "panels": [
                        {
                            "id": "panel-two",
                            "name": "Other",
                            "reportSuite": component("dv-two", "ReportSuite"),
                            "subPanels": [
                                {
                                    "id": "text",
                                    "name": "Notes",
                                    "reportlet": {
                                        "type": "TextReportlet",
                                        "textContent": TextBuilder()
                                        .addBold("Hello")
                                        .to_json(),
                                    },
                                }
                            ],
                            "segmentGroups": [
                                {
                                    "componentOptions": [
                                        {
                                            "component": component(
                                                "s-other", "Segment"
                                            ),
                                            "isActive": True,
                                        },
                                    ]
                                }
                            ],
                        }
                    ],
                },
            ],
        },
    }


def ids(components):
    return {comp["id"] for comp in components}


def test_lossless_all_workspaces_and_scoped_aggregates():
    data = project_fixture()
    original = deepcopy(data)
    manager = WorkspaceManager(data=data)
    assert manager.to_dict() == original == data
    assert manager.project_details == original
    assert manager.project_id == "project-id"
    assert manager.nbPanels == 2 and manager.nbSubPanels == 4
    assert [ws.id for ws in manager.workspaces] == ["workspace-one", "workspace-two"]
    assert ids(manager.segments) == {
        "s-active",
        "s-inactive",
        "s-column",
        "s-deep",
        "s-other",
    }
    assert ids(manager.calculatedMetrics) == {"cm-curated"}
    assert ids(manager.dataViews) == {"dv-one", "dv-two"}
    panel = manager.panels[0]
    assert ids(panel.segments) == {"s-active", "s-inactive", "s-column", "s-deep"}
    assert ids(panel.activeFilters) == {"s-active", "variables/filter"}
    assert panel.elements[0].workspaceId == "workspace-one"
    assert panel.elements[0].dataViewId == "dv-one"
    assert isinstance(panel.elements[0].reportlet, FreeForm)
    chart = panel.elements[1]
    assert isinstance(chart.reportlet, LineReportlet)
    assert chart.linkedSource is panel.elements[0]
    assert ids(chart.metrics) == {"metrics/events"}
    assert ids(chart.segments) == {"s-column"}
    assert ids(chart.dimensions) == {"variables/page", "variables/device"}
    assert ids(panel.elements[2].dimensions) == {"variables/flow"}
    assert manager.panels[1].elements[0].text == "Hello"
    result = manager.to_dict()
    result["definition"]["workspaces"].clear()
    assert len(manager.workspaces) == 2


@pytest.mark.parametrize("encoding", ["dimension", "dimensions", "dimensionSettings"])
def test_freeform_legacy_and_current_row_formats_roundtrip(encoding):
    raw = FreeForm.build(
        "Table",
        [{"id": "metrics/events"}],
        items=[
            {"id": "s-row", "name": "Row", "type": "Segment"},
        ],
    ).to_dict()
    dim = component("variables/a", "Dimension")
    raw["freeformTable"][encoding] = (
        [{"id": "setting", "dimension": dim}]
        if encoding == "dimensionSettings"
        else [dim]
        if encoding == "dimensions"
        else dim
    )
    raw["advancedMode"] = True
    raw["advancedSettings"] = {
        "tableState": "done",
        "rows": [
            {
                "key": "advanced",
                "components": [component("variables/a::item", "DimensionItem")],
            }
        ],
    }
    raw["advancedSettings"]["originalColumnTree"] = {
        "nodes": [
            {"component": component("cm-original", "CalculatedMetric"), "nodes": []}
        ],
    }
    raw["customTableState"] = {"keep": "value"}
    ff = FreeForm.from_dict(raw)
    assert ff.to_dict() == raw
    assert ff.dimension == dim
    assert ids(ff.dimensionItems) == {"variables/a::item"}
    assert ff.advancedRows[0]["key"] == "advanced"
    assert ids(ff.calculatedMetrics) == {"cm-original"}


def test_nested_breakdowns_preserve_parent_ids_and_custom_settings():
    raw = project_fixture()["definition"]["workspaces"][0]["panels"][0]["subPanels"][0][
        "reportlet"
    ]
    ff = FreeForm.from_dict(raw)
    assert ff.to_dict() == raw
    assert ff.breakdowns[0].parentItemId == "42"
    assert ff.breakdowns[0].breakdowns[0].parentItemIds == ["a", "b"]
    assert ids(ff.dimensions) >= {
        "variables/channel",
        "variables/country",
        "variables/device",
    }


def test_dynamic_breakdowns_require_real_row_identity_and_sync_nested_changes():
    manager = WorkspaceManager(dataViewId="dv", name="Built").addPanel("Overview")
    ff = manager.addFreeform(
        "Table", item_id="variables/page", metrics=[{"id": "metrics/events"}]
    )
    before = manager.to_dict()
    with pytest.raises(ValueError, match="real parent_item_id"):
        ff.addBreakdown("variables/device")
    assert manager.to_dict() == before
    child = ff.addBreakdown("variables/device", parent_item_id="item-42")
    child.addBreakdown(
        items=[{"id": "s-child", "name": "Nested"}], parent_item_id="device-7"
    )
    raw = manager.to_dict()["definition"]["workspaces"][0]["panels"][0]["subPanels"][0][
        "reportlet"
    ]
    assert raw["freeformTable"]["breakdowns"][0]["parentItemIds"] == ["item-42"]
    assert raw["freeformTable"]["breakdowns"][0]["breakdowns"][0]["parentItemIds"] == [
        "device-7"
    ]
    assert ids(ff.segments) == {"s-child"}
    assert ids(manager.segments) == {"s-child"}


def test_static_filter_rows_break_down_every_row_and_preserve_loaded_project():
    original = project_fixture()
    manager = WorkspaceManager(data=original).selectWorkspace(1)
    manager.addSegmentAsDimensionFreeform(
        "Comparison",
        [{"id": "s-a", "name": "A"}, {"id": "s-b", "name": "B"}],
        [{"id": "metrics/events", "name": "Events"}],
        breakdown_dim_id="variables/device",
    )
    ff = manager.panels[1].elements[-1].freeform
    assert [child.parentItemId for child in ff.breakdowns] == [
        row["id"] for row in ff.staticRows
    ]
    manager.addBreakdownToDimension("variables/channel", target="Comparison")
    assert len(manager.panels[1].elements[-1].freeform.breakdowns) == 4
    assert (
        manager.to_dict()["definition"]["workspaces"][0]
        == original["definition"]["workspaces"][0]
    )


def test_text_builder_and_import_formats(tmp_path):
    builder = (
        TextBuilder()
        .addTitle("Title")
        .addText("Plain")
        .addBold("Bold")
        .addItalic("Italic")
        .addUnderline("Under")
        .addColor("Color", "#fff")
        .addLink("Link", "https://example.com")
        .addNewline()
    )
    manager = WorkspaceManager(rsid="dv", name="Example").addPanel("Panel")
    manager.addTextFreeform("Rich", builder).addTextFreeform("Plain", "Note")
    manager.addTextFreeform("Delta", builder.to_dict())
    assert manager.panels[0].elements[0].textOps == builder.to_dict()["ops"]
    assert manager.panels[0].elements[1].text == "Note\n"
    path = tmp_path / "project.json"
    encoded = manager.to_json(path)
    assert WorkspaceManager(data=path).to_dict() == manager.to_dict()
    assert WorkspaceManager(data=encoded).to_dict() == manager.to_dict()
    assert (
        WorkspaceManager(project_details=manager.to_dict()).to_dict()
        == manager.to_dict()
    )
    result = builder.to_dict()
    result["ops"].clear()
    assert builder.to_dict()["ops"]


@pytest.mark.parametrize(
    "content",
    ["not JSON", {"ops": [{"insert": "Text"}, {"insert": {"image": "image"}}]}],
)
def test_unusual_text_keeps_raw_content_and_reports_parse_warning(content):
    raw = {"type": "TextReportlet", "textContent": content}
    text = Reportlet.from_dict(raw)
    assert isinstance(text, TextReportlet)
    assert text.to_dict() == raw
    assert text.text == ("not JSON" if isinstance(content, str) else "Text")
    assert bool(text.parseWarnings) == isinstance(content, str)


def test_unknown_reportlet_and_unresolved_chart_are_preserved():
    raw = {
        "id": "sub",
        "reportlet": {
            "type": "FutureReportlet",
            "component": component("metrics/new", "Metric"),
        },
        "linkedSourceId": "missing",
    }
    data = {
        "definition": {"workspaces": [{"panels": [{"id": "p", "subPanels": [raw]}]}]}
    }
    manager = WorkspaceManager(data=data)
    panel = manager.panels[0].elements[0]
    assert type(panel.reportlet) is Reportlet
    assert ids(panel.metrics) == {"metrics/new"}
    assert panel.parseWarnings == ["Unresolved linkedSourceId: missing"]
    assert manager.to_dict() == data


def test_cja_api_resolution_is_lazy_cached_and_scoped_to_current_data_view():
    cja = Mock()
    cja.getMetrics.return_value = [{"id": "metrics/events", "name": "Events"}]
    cja.getCalculatedMetrics.return_value = []
    cja.getDimensions.return_value = [{"id": "variables/page", "name": "Page"}]
    cja.getFilters.return_value = [{"id": "s-person", "name": "Audience"}]
    manager = WorkspaceManager(dataViewId="dv-one", name="Example", cja=cja)
    assert not cja.mock_calls
    manager.addPanel("One").addFilter(name="Audience")
    manager.addFreeform("Traffic", item_name="Page", metrics=[{"name": "Events"}])
    manager.addFreeform("More", item_name="Page", metrics=[{"name": "Events"}])
    cja.getDimensions.assert_called_once_with(dataviewId="dv-one", output="raw")
    cja.getMetrics.assert_called_once_with(dataviewId="dv-one", output="raw")
    cja.getFilters.assert_called_once_with(dataIds="dv-one", output="raw")
    manager.addPanel("Two", dataViewId="dv-two")
    manager.addFreeform(
        "Other", item_id="variables/page", metrics=[{"id": "metrics/events"}]
    )
    assert cja.getMetrics.call_args.kwargs["dataviewId"] == "dv-two"


def test_charts_summary_numbers_and_wire_names():
    manager = WorkspaceManager(dataViewId="dv", name="Example").addPanel("Panel")
    manager.addFreeform(
        "Traffic", item_id="variables/page", metrics=[{"id": "metrics/events"}]
    )
    manager.addChart("bar_stacked", source="Traffic")
    manager.addSummaryNumber("Total", metric="metrics/events")
    panel = manager.panels[0]
    assert isinstance(panel.elements[1].reportlet, BarStackedReportlet)
    assert panel.elements[2].reportletType == "SummaryNumberReportlet"
    assert ids(panel.elements[2].metrics) == {"metrics/events"}
    assert panel.elements[2].linkedSource is panel.elements[3]
    raw = manager.to_dict()
    assert raw["dataId"] == "dv" and "rsid" not in raw
    assert (
        raw["definition"]["workspaces"][0]["panels"][0]["reportSuite"]["__metaData__"][
            "rsid"
        ]
        == "dv"
    )
    assert "dimension" not in panel.elements[0].freeform.to_dict()["freeformTable"]
    with pytest.raises(ValueError, match="source"):
        manager.addChart("line", source=1)
    with pytest.raises(NotImplementedError):
        manager.addSummaryNumber("Change", metric="metrics/events", show_change=True)


def test_create_update_validate_and_persisted_id_checks():
    cja = Mock()
    cja.createProject.return_value = {"id": "created-id"}
    manager = WorkspaceManager(dataViewId="dv", name="Example", cja=cja)
    manager.addPanel("Panel").setOwner("ims-user").addTag(1).addShare(
        share_to_type="all"
    )
    with pytest.raises(ValueError, match="persisted"):
        manager.updateProject()
    with pytest.warns(UserWarning, match="tags/shares"):
        assert manager.createProject() == {"id": "created-id"}
    payload = cja.createProject.call_args.args[0]
    assert "id" not in payload and "tags" not in payload and "shares" not in payload
    assert payload["dataId"] == "dv" and payload["owner"] == {"imsUserId": "ims-user"}
    assert manager.to_dict()["id"] == "created-id"
    with pytest.raises(ValueError, match="already"):
        manager.createProject()
    with pytest.warns(UserWarning, match="tags/shares"):
        manager.updateProject()
    cja.updateProject.assert_called_once_with("created-id", payload)
    with pytest.warns(UserWarning, match="tags/shares"):
        manager.validateProject()
    cja.validateProject.assert_called_once_with(payload)
    with pytest.raises(ValueError, match="connection"):
        WorkspaceManager(dataViewId="dv", name="Offline").createProject()


def test_replace_data_view_is_scoped_and_leaves_components_unchanged():
    manager = WorkspaceManager(data=project_fixture())
    manager.replaceDataView("dv-new", "New View", oldDataViewId="dv-two")
    assert [p.dataViewId for p in manager.panels] == ["dv-one", "dv-new"]
    assert manager.dataViewId == "dv-one"
    assert ids(manager.metrics) == {"metrics/events"}
    manager.replaceDataView("dv-all", "All Views")
    assert {p.dataViewId for p in manager.panels} == {"dv-all"}
    assert manager.to_dict()["dataId"] == "dv-all"


def test_get_project_workspace_manager_opt_in(client):
    data = project_fixture()
    client.connector.getData.return_value = data
    manager = client.getProject("project-id", workspaceManager=True)
    assert isinstance(manager, WorkspaceManager)
    assert manager.to_dict() == data
    assert client.connector.getData.call_args.kwargs["params"]["expansion"].endswith(
        "definition"
    )
    assert cjapy.WorkspaceManager is WorkspaceManager


@pytest.mark.parametrize("rows", [0, -1, True, 1.5])
def test_invalid_rows_do_not_modify_project(rows):
    manager = WorkspaceManager(dataViewId="dv", name="Example").addPanel("Panel")
    before = manager.to_dict()
    with pytest.raises(ValueError, match="positive"):
        manager.addFreeform(
            "Bad",
            item_id="variables/page",
            metrics=[{"id": "metrics/events"}],
            rows=rows,
        )
    assert manager.to_dict() == before


def test_filters_and_column_nodes_have_unique_ids():
    ff = FreeForm.build(
        "Filtered",
        [
            {
                "id": "metrics/events",
                "filters": [
                    {"id": "variables/page::a", "name": "A", "type": "DimensionItem"},
                    {"id": "variables/page::b", "name": "B", "type": "DimensionItem"},
                    {"id": "s-filter", "name": "Filter", "type": "Segment"},
                ],
            }
        ],
        dim_id="variables/device",
    )
    nodes = ff.columnTree["nodes"]
    first_ids = [
        nodes[0]["id"],
        nodes[0]["nodes"][0]["id"],
        nodes[0]["nodes"][0]["nodes"][0]["id"],
    ]
    second_ids = [
        nodes[1]["id"],
        nodes[1]["nodes"][0]["id"],
        nodes[1]["nodes"][0]["nodes"][0]["id"],
    ]
    assert len(set(first_ids + second_ids)) == 6
    assert ids(ff.dimensionItems) == {"variables/page::a", "variables/page::b"}
    assert ff.freeformTable["sort"]["columnId"] == nodes[0]["nodes"][0]["id"]
    child = ff.addBreakdown("variables/page", parent_item_id="device-42")
    assert (
        child.freeformTable["sort"]["columnId"] == ff.freeformTable["sort"]["columnId"]
    )
    assert child.freeformTable["columnWidths"] == ff.freeformTable["columnWidths"]


def test_legacy_unnamed_and_position_based_breakdowns_are_lossless():
    raw = {
        "type": "FreeformReportlet",
        "columnTree": {"nodes": []},
        "freeformTable": {
            "staticRows": [],
            "breakdowns": [
                {
                    "parentPosition": 3,
                    "settings": {"breakdownByPosition": True},
                    "staticRows": [],
                    "breakdowns": [],
                }
            ],
        },
    }
    ff = FreeForm.from_dict(raw)
    assert ff.to_dict() == raw
    assert ff.breakdowns[0].parentPosition == 3
    assert ff.breakdowns[0].breakdownByPosition is True


def test_guided_analysis_references_and_mobile_scorecard_components():
    raw = {
        "type": "guidedAnalysis",
        "dataId": "dv",
        "definition": {
            "events": [
                {
                    "metricId": "cm-conversion",
                    "name": "Conversion",
                    "filters": [
                        {
                            "dimensionId": "variables/page",
                            "dimensionName": "Page",
                            "dimensionItems": [{"itemId": "42", "value": "Home"}],
                        }
                    ],
                }
            ],
            "peopleSegments": [
                {"id": "local", "segmentId": "s-audience", "name": "Audience"}
            ],
        },
    }
    manager = WorkspaceManager(data=raw)
    assert manager.to_dict() == raw
    assert ids(manager.calculatedMetrics) == {"cm-conversion"}
    assert ids(manager.dimensionItems) == {"variables/page::42"}
    assert ids(manager.segments) == {"s-audience"}
    assert ids(manager.dataViews) == {"dv"}
    assert manager.panels == []
    with pytest.raises(ValueError, match="desktop"):
        manager.addPanel("Not a workspace")
    mobile = WorkspaceManager(
        data={
            "type": "mobileScorecard",
            "definition": {
                "screens": [
                    {
                        "slides": [
                            {
                                "panels": [
                                    {
                                        "modules": [
                                            {
                                                "content": {
                                                    "kpi": {
                                                        "metric": component(
                                                            "metrics/events", "Metric"
                                                        )
                                                    }
                                                }
                                            },
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
            },
        }
    )
    assert ids(mobile.metrics) == {"metrics/events"}


def test_id_and_name_resolution_avoids_cross_data_view_labels_and_ambiguity():
    raw = project_fixture()
    manager = WorkspaceManager(data=raw).selectWorkspace(1)
    with pytest.raises(ValueError, match="found 0"):
        manager.addFreeform(
            "Wrong view", item_name="Page", metrics=[{"id": "metrics/events"}]
        )
    manager.addFilter(filter_id="s-local", name="Subscribers")
    manager.addSegmentFilter("Subscribers")
    assert (
        manager.panels[1].segmentGroups[-1]["componentOptions"][0]["component"]["id"]
        == "s-local"
    )
    manager.addSummaryNumber("Custom", metric="_tenant.event")
    assert ids(manager.panels[1].elements[-2].metrics) == {"_tenant.event"}


def test_live_table_handles_survive_manager_breakdown_edits():
    manager = WorkspaceManager(dataViewId="dv", name="Example").addPanel("Panel")
    table = manager.addFreeform(
        "Table",
        items=[{"id": "s-a", "name": "A", "type": "Segment"}],
        metrics=[{"id": "metrics/events"}],
    )
    child = table.addBreakdown("variables/device")
    manager.addBreakdownToDimension("variables/channel", target="Table")
    child.addBreakdown("variables/country", parent_item_id="device-42")
    assert manager.getFreeform("Table") is table
    raw = manager.to_dict()["definition"]["workspaces"][0]["panels"][0]["subPanels"][0][
        "reportlet"
    ]
    assert len(raw["freeformTable"]["breakdowns"]) == 2
    assert len(raw["freeformTable"]["breakdowns"][0]["breakdowns"]) == 1
    loaded = WorkspaceManager(data=manager.to_dict())
    loaded.getFreeform("Table").addBreakdown("variables/browser")
    assert len(loaded.panels[0].elements[0].freeform.breakdowns) == 3


def test_local_customer_corpus_roundtrip_when_available():
    directory = Path(__file__).resolve().parents[1] / "Projects"
    files = sorted(directory.glob("*.json"))
    if not files:
        pytest.skip("Optional anonymized customer corpus is not distributed.")
    # Small deterministic fixture sample for CI; a separate full-corpus check is
    # used during development without copying customer definitions into tests.
    for path in files[:3]:
        data = json.loads(path.read_text(encoding="utf-8"))
        manager = WorkspaceManager(data=data)
        assert manager.to_dict() == data
        assert manager.nbPanels == len(manager.panels)
