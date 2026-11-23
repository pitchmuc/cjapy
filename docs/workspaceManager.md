# cjapy : WorkspaceManager class

The `WorkspaceManager` class enables you to read, edit, and create Analysis Workspace project definitions.\
You can inspect the panels and components used in an existing project, or build a new project before sending it to CJA.

**NOTE**: This class works with project definitions, not report results. For the class returned by `getReport`, see [Workspace](workspace.md).\
The [Project class](projects.md) provides another way to inspect the components used in existing projects.

## Menu

* [WorkspaceManager instantiation](#workspacemanager-instantiation)
* [Attributes of WorkspaceManager](#attributes-of-workspacemanager)
* [Methods available on WorkspaceManager](#methods-available-on-workspacemanager)
* [FreeForm class](#freeform-class)
* [TextBuilder class](#textbuilder-class)
* [Creating a Workspace project](#creating-a-workspace-project)
* [Publishing a Workspace project](#publishing-a-workspace-project)

## WorkspaceManager instantiation

You can create an instance from an existing project definition or start with an empty project.

Arguments:

* data : OPTIONAL : Existing project as an API response dictionary, definition dictionary, JSON string, file path, or `pathlib.Path`.
* dataViewId : OPTIONAL : Data View ID. Required when creating a new project.
* name : OPTIONAL : Project name. Required when creating a new project.
* description : OPTIONAL : Project description.
* tags : OPTIONAL : List of tag IDs or tag dictionaries to add to the local project.
* shares : OPTIONAL : List of sharing dictionaries to add to the local project.
* cja : OPTIONAL : Existing `CJA` instance to use for component lookups and API operations.
* config : OPTIONAL : Configuration object used to create a `CJA` connection when `cja` is not provided.
* project_details : OPTIONAL : Alias for `data`. Do not provide both arguments.
* rsid : OPTIONAL : Compatibility alias for `dataViewId`.
* analytics : OPTIONAL : Compatibility alias for `cja`.
* companyId : OPTIONAL : Accepted for compatibility with `aanalytics2`; not used by CJA.

### Loading an existing project

You can load a project saved in a JSON file without connecting to CJA:

```python
import cjapy

myWorkspace = cjapy.WorkspaceManager(data=r"Projects\project.json")
```

With an authenticated `CJA` instance, you can also retrieve a project directly:

```python
import cjapy

cjapy.importConfigFile("myConfig.json")
cja = cjapy.CJA()
myWorkspace = cja.getProject("project-id", workspaceManager=True)
```

The default `getProject` behavior and the `projectClass=True` option are unchanged.

**NOTE**: Loading and inspecting a definition do not make API requests, even when a `cja` connection is attached. Unknown fields, older schema versions, positions, IDs, and metadata are preserved.

### Creating an empty project

To create a new project, provide its name and Data View ID:

```python
import cjapy

myWorkspace = cjapy.WorkspaceManager(
    dataViewId="dv-example",
    name="Overview",
)
```

You can build the project offline with explicit component IDs and names.\
With `cja` provided, missing names or name-only inputs can be resolved through `getDimensions`, `getMetrics`, `getCalculatedMetrics`, `getFilters`, and `getDateRanges`. These lookups are cached per data view and use the connection's existing retry and proxy configuration. Ambiguous names require an ID.\
Without a connection, an ID uses an embedded or cached name when available, otherwise the ID itself as its label.

## Attributes of WorkspaceManager

### id, project_id, name and description

`id` is the project ID returned by CJA; `project_id` is an alias. A new project has no ID until it is created through the API.\
`name` and `description` contain the project title and description.

### dataViewId and dataViewName

These attributes contain the project's Data View ID and name. Individual panels can use different data views.\
`rsid` and `rsid_name` are compatibility aliases for these attributes.

### owner, created, modified and version

These attributes expose the owner, creation date, modification date, and definition version from the loaded project.\
Other project metadata is available through `approved`, `companyTemplate`, `organizationTemplate`, `tags`, and `shares`.

### definition and project_details

`definition` gives direct access to the mutable Workspace definition. Changes to this dictionary edit the project.\
`project_details` returns a detached copy of the full project dictionary, including metadata. Changing that copy does not edit the project.

### workspaces and panels

`workspaces` returns a list of `WorkspaceDefinition` instances. Each instance provides `id`, `name`, `panels`, and `raw`.\
`panels` returns the panels from all workspaces, not only the selected workspace.

Both attributes are recomputed on access and return detached inspection snapshots. To edit a table, use `getFreeform` instead of modifying a snapshot.

```python
for workspace in myWorkspace.workspaces:
    print(workspace.id, workspace.name)
    for panel in workspace.panels:
        print(panel.name, panel.dataViewId)
        for element in panel.elements:
            print(element.name, element.type, element.reportletType)
```

Container panels have `type == "SubPanel"` and hold their visualizations in `elements`. Leaf types are `"FreeForm"`, `"Text"`, or `"Visualization"`.\
The following attributes are available on panels:

* id, name, description, position, collapsed, visible : Panel identification and display settings.
* workspaceId, dataViewId, dataViewName, rsid : Workspace and data-view information.
* dateRange, segmentGroups, activeFilters : Date selection and filters on container panels.
* reportletType, reportlet : Reportlet type and its typed wrapper.
* freeform, text, textOps, chartType : Table, text, or chart information where applicable.
* linkedSourceId, linkedSource : Source table used by a linked visualization.
* parseWarnings : Parsing issues, such as a missing source link or malformed text.
* raw : Underlying panel dictionary in the inspection snapshot.

`reportlet` provides wrappers such as `FreeformReportlet` (an alias of `FreeForm`), `TextReportlet`, `SummaryNumberReportlet`, `SummaryChangeReportlet`, `LineReportlet`, `BarReportlet`, and `DonutReportlet`.\
Other chart types, Flow, Fallout, cohort, journey canvas, and map definitions also have typed wrappers. Unknown types use `Reportlet` and retain their full JSON. Reportlet-specific properties are available through the wrapper, and `raw` provides the underlying definition.

### nbPanels and nbSubPanels

These attributes provide the number of panels and sub-panels across all workspaces in the project.

### components

`components` returns the deduplicated component lists used in the project. Each entry contains an `id` and a `name`.\
The lists are also available individually as `dimensions`, `dimensionItems`, `metrics`, `calculatedMetrics`, `segments`, `dateRanges`, `dataViews`, `annotations`, and `attributionTemplates`. `filters` is an alias for `segments`.

The same attributes are available on workspace, panel, and reportlet instances.\
`dimensions` includes dimension-item IDs for compatibility with `aanalytics2`; `dimensionItems` provides those items separately.

**NOTE**: These lists describe definition dependencies, not only what is currently displayed. They include curated components, standalone visualizations, and advanced-table editor state (`originalColumnTree`). Panel components include all dropdown options; use `activeFilters` to inspect active options and dynamic dimensions.\
Linked charts resolve selected columns through their source table, including ancestor filters. Unlocked charts inherit the source components.

## Methods available on WorkspaceManager

Methods that add or select content operate on the selected workspace and panel.\
The editing methods below return the `WorkspaceManager` instance, except `addFreeform` and `getFreeform`, which return a live `FreeForm` instance.

### addWorkspace

Add a workspace and select it for subsequent operations.

Arguments:

* name : OPTIONAL : Workspace name. Default is an empty string.

### selectWorkspace

Select an existing workspace.

Arguments:

* workspace : REQUIRED : Workspace index, ID, or name.

### selectPanel

Select an existing panel in the current workspace.

Arguments:

* panel : REQUIRED : Panel index, ID, or name.

### addPanel

Add a panel and select it for subsequent operations.

Arguments:

* name : REQUIRED : Panel name.
* date_range : OPTIONAL : Date-range ID or ISO date interval. Default is `"thisMonth"`. Built-in presets also include `"lastFullMonth"`, `"thisWeek"`, `"lastFullWeek"`, `"today"`, and `"yesterday"`.
* position : OPTIONAL : Insertion index in the panel list.
* collapsed : OPTIONAL : Whether the panel is collapsed. Default is `False`.
* description : OPTIONAL : Panel description.
* dataViewId : OPTIONAL : Data View ID for this panel. Defaults to the project's data view.
* dataViewName : OPTIONAL : Display name for the panel's data view.

### addTextFreeform

Add a text visualization to the selected panel.

Arguments:

* title : REQUIRED : Visualization title.
* content : REQUIRED : Plain text, a `TextBuilder`, or a Quill Delta dictionary or JSON string. An `aanalytics2` `TextBuilder` is also accepted.
* collapsed : OPTIONAL : Whether the visualization is collapsed. Default is `False`.
* description : OPTIONAL : Visualization description.

### addFreeform

Add a freeform table with dynamic dimension rows or static component rows.\
This method returns a live `FreeForm` instance. Calling its `addBreakdown` method updates the project immediately.

Arguments:

* title : REQUIRED : Table title.
* item_id : OPTIONAL : Dimension or component ID. Provide this or `item_name` when not using `items`.
* item_name : OPTIONAL : Dimension or component name.
* items : OPTIONAL : List of static row component dictionaries. Do not combine with `item_id` or `item_name`.
* metrics : REQUIRED : Non-empty list of metric dictionaries.
* rows : OPTIONAL : Number of rows to display. Default is `10`.
* collapsed : OPTIONAL : Whether the table is collapsed. Default is `False`.
* description : OPTIONAL : Table description.

Metric dictionaries accept `id`, `name`, and `filters`. Filter dictionaries accept `id`, `name`, and an optional `type`, such as `"Segment"`, `"DimensionItem"`, or `"DateRange"`.\
Static row dictionaries can specify `type` explicitly. Otherwise, IDs such as `variables/...` identify dimensions, `::` identifies dimension items, and segment IDs identify filters. Use an explicit type for nonstandard IDs.

### getFreeform

Return a live editable table from the selected panel, including tables in a loaded project.

Arguments:

* source : OPTIONAL : Sub-panel ID, name, or index. Defaults to the last freeform table.

### addActivityBreakdownFreeform

Add a table with a fixed dimension item and a dimension breakdown. This can use any dimension item; it does not require Adobe Target.

Arguments:

* title : REQUIRED : Table title.
* activity_dim_item_id : REQUIRED : Dimension-item ID.
* activity_name : REQUIRED : Dimension-item display name.
* breakdown_dim_id : REQUIRED : Breakdown dimension ID.
* breakdown_dim_name : REQUIRED : Breakdown dimension name.
* metrics : REQUIRED : List of metric dictionaries.
* rows : OPTIONAL : Number of table rows. Default is `50`.
* breakdown_rows : OPTIONAL : Number of breakdown rows. Default is `5`.
* collapsed : OPTIONAL : Whether the table is collapsed. Default is `False`.
* description : OPTIONAL : Table description.

### addSegmentAsDimensionFreeform

Add a table with CJA filters as static rows, optionally with a breakdown under each row.

Arguments:

* title : REQUIRED : Table title.
* segments : REQUIRED : List of filter dictionaries containing IDs and/or names.
* metrics : REQUIRED : List of metric dictionaries.
* breakdown_dim_id : OPTIONAL : Breakdown dimension ID.
* breakdown_dim_name : OPTIONAL : Breakdown dimension name.
* breakdown_segments : OPTIONAL : Filters to use as breakdown rows instead of a dimension. Do not combine with a dimension breakdown.
* breakdown_rows : OPTIONAL : Number of breakdown rows. Default is `5`.
* rows : OPTIONAL : Number of table rows. Default is `50`.
* collapsed : OPTIONAL : Whether the table is collapsed. Default is `False`.
* description : OPTIONAL : Table description.

### addBreakdownToDimension

Add a dimension breakdown to existing tables in the selected panel while preserving their metadata.

Arguments:

* breakdown_dim_id : OPTIONAL : Breakdown dimension ID. Provide an ID or a name.
* breakdown_dim_name : OPTIONAL : Breakdown dimension name.
* target : OPTIONAL : Table sub-panel ID, name, or index; `"all"` for all freeform tables; or `None` for the last table. Default is `"all"`.
* breakdown_rows : OPTIONAL : Number of breakdown rows. Default is `5`.
* parent_item_id : OPTIONAL : Row item ID to break down. Required for dynamic rows. When omitted for static tables, a breakdown is added under every static row.

### addSegmentFilter

Add a CJA filter to the selected panel.

Arguments:

* segment : REQUIRED : Filter ID or name.

### addFilter

Add a CJA filter to the selected panel using separate ID and name arguments.

Arguments:

* filter_id : OPTIONAL : Filter ID. Provide an ID or a name.
* name : OPTIONAL : Filter name.

### addDropdownFilter

Add a dropdown filter group to the selected panel.

Arguments:

* group_name : REQUIRED : Dropdown group name.
* components : REQUIRED : Non-empty list of component dictionaries. An option can specify `isActive`; otherwise the first option is selected.
* has_no_filter : OPTIONAL : Whether the dropdown includes a "No filter" option. Default is `True`.

At most one option can be active. When `has_no_filter=False`, exactly one option must be active.

### addChart

Add a chart linked to a freeform table in the selected panel.

Arguments:

* viz_type : REQUIRED : Chart type: `"line"`, `"bar"`, `"bar_horizontal"`, `"bar_stacked"`, `"bar_horizontal_stacked"`, `"area"`, `"area_stacked"`, `"donut"`, `"scatter"`, `"treemap"`, `"histogram"`, `"bullet"`, `"venn"`, or `"combo"`.
* source : OPTIONAL : Source table sub-panel ID, name, or index. Defaults to the last freeform table.
* title : OPTIONAL : Chart title.
* collapsed : OPTIONAL : Whether the chart is collapsed. Default is `False`.
* description : OPTIONAL : Chart description.

### addSummaryNumber

Add a summary number with an automatically linked backing table.

Arguments:

* title : REQUIRED : Visualization title.
* metric : REQUIRED : Metric ID or name.
* collapsed : OPTIONAL : Whether the visualization is collapsed. Default is `False`.
* description : OPTIONAL : Visualization description.
* show_change, show_percent_change, show_sparkline : OPTIONAL : Compatibility arguments, all `False` by default. Setting any of them to `True` raises `NotImplementedError`.

### replaceDataView

Replace all or selected data-view references in the project.

Arguments:

* dataViewId : REQUIRED : New Data View ID.
* name : OPTIONAL : New data-view display name.
* oldDataViewId : OPTIONAL : Restrict replacement to this Data View ID. By default, all data-view references are replaced.

**NOTE**: This method does not translate dimension, metric, calculated-metric, or filter IDs between data views. Use compatible components and validate against the target view before publishing.

### setOwner

Set the project owner.

Arguments:

* owner : REQUIRED : IMS user ID string, legacy numeric user ID, or owner dictionary.

### addTag

Add a tag to the local project metadata without duplicating an existing tag ID.

Arguments:

* tag : REQUIRED : Numeric tag ID or dictionary containing an `id`.

### addShare

Add a sharing entry to the local project metadata.

Arguments:

* share_to_id : OPTIONAL : User or group ID. Required unless `share_to_type` is `"all"`.
* share_to_type : OPTIONAL : `"user"`, `"group"`, or `"all"`. Default is `"user"`.
* share_to_display_name : OPTIONAL : Display name for the sharing entry.

**NOTE**: Tags and shares remain local metadata. The Projects API does not write them through project creation or update bodies.

### to_dict

Return a detached dictionary of the full project, including metadata and unknown fields. Changing the returned dictionary does not edit the instance.

### to_json

Return the full project as a JSON string and optionally save it to a file.

Arguments:

* filename : OPTIONAL : File path to write, as a string or `pathlib.Path`.

### validateProject

Send the project to `CJA.validateProject` and return Adobe's compatibility result. Requires a CJA connection.\
Inspect the result before deciding whether to create or update the project.

### createProject

Create the project in CJA and return the API response. Requires a CJA connection and a project without an ID.\
The returned ID is saved on the instance for subsequent updates.

### updateProject

Update the project in CJA and return the API response. Requires a CJA connection and an existing project ID.

## FreeForm class

The `FreeForm` instance represents a freeform table. You can inspect it through a panel's `freeform` attribute, or edit a live instance returned by `addFreeform` or `getFreeform`.

### Attributes of FreeForm

The table supports legacy `dimension` and `dimensions` definitions, current `dimensionSettings`, static rows, advanced-mode rows, nested column filters, and nested breakdowns.

* title, dimension, dimensionSettings : Table title and dimension configuration.
* staticRows, advancedRows, rows : Row definitions and row settings.
* columnTree : Metric columns and their nested filters.
* breakdowns : Child `FreeForm` instances.
* parentItemId, parentItemIds, breakdownByPosition : Parent-row references and breakdown settings.

The component attributes described above are also available on the table.

### addBreakdown

Add a breakdown and return the child `FreeForm`. On a live table, this also updates the owning project. Further breakdowns on the returned child update the same project.

Arguments:

* dimension_id : OPTIONAL : Breakdown dimension ID. Provide this or non-empty `items`, not both.
* dimension_name : OPTIONAL : Breakdown dimension display name.
* items : OPTIONAL : Static component rows to use instead of a dimension.
* rows : OPTIONAL : Number of breakdown rows. Default is `5`.
* parent_item_id : OPTIONAL : Item ID of the row to break down. Defaults to the first static row. For dynamic rows, provide a real item ID from a CJA report.

Use `to_dict()` to return the table definition.

## TextBuilder class

`TextBuilder` creates formatted text for `addTextFreeform` using the Quill Delta format.

```python
myText = cjapy.TextBuilder()
myText.addTitle("Overview").addText("A note.\n").addBold("Important")
myWorkspace.addTextFreeform("Notes", myText)
```

### Methods available on TextBuilder

The formatting methods return the same `TextBuilder` instance so that calls can be chained.

* `addTitle(text, level=2)` : Add a heading. `text` is REQUIRED; `level` is OPTIONAL and defaults to `2`.
* `addText(text)` : Add plain text. `text` is REQUIRED.
* `addBold(text)` : Add bold text. `text` is REQUIRED.
* `addItalic(text)` : Add italic text. `text` is REQUIRED.
* `addUnderline(text)` : Add underlined text. `text` is REQUIRED.
* `addColor(text, color)` : Add colored text. Both arguments are REQUIRED.
* `addLink(text, url)` : Add a link. Both arguments are REQUIRED.
* `addNewline()` : Add a line break.
* `to_dict()` : Return the Delta as a dictionary.
* `to_json()` : Return the Delta as a JSON string.

## Creating a Workspace project

The following example creates an offline project with a panel, a table, a linked chart, and a summary number:

```python
import cjapy

myWorkspace = cjapy.WorkspaceManager(dataViewId="dv-example", name="Overview")
myWorkspace.addPanel("Traffic", date_range="thisMonth")
myTable = myWorkspace.addFreeform(
    "Events by page",
    item_id="variables/page",
    item_name="Page",
    metrics=[{"id": "metrics/occurrences", "name": "Events"}],
)
myWorkspace.addChart("line", source="Events by page", title="Trend")
myWorkspace.addSummaryNumber("Total events", metric="metrics/occurrences")
myDefinition = myWorkspace.to_dict()
```

Replace the example IDs with components from your data view. To break down a dynamic table row, use an actual item ID returned by a CJA report:

```python
myTable.addBreakdown(
    dimension_id="variables/device",
    dimension_name="Device",
    parent_item_id="actual-page-item-id",
)
```

**NOTE**: New projects use `dataId` at the root. Inside panels, the CJA definition still uses `reportSuite`, component type `ReportSuite`, and metadata `rsid`. These values are Data View IDs, not Adobe Analytics report suites.\
New tables and breakdowns use `dimensionSettings` and `parentItemIds`. Loaded definitions retain their original schema and unknown fields.

## Publishing a Workspace project

Attach an authenticated CJA connection when creating the instance to enable validation and publication:

```python
import cjapy

cjapy.importConfigFile("myConfig.json")
cja = cjapy.CJA()
myWorkspace = cjapy.WorkspaceManager(
    dataViewId="dv-example",
    name="Overview",
    cja=cja,
)
myWorkspace.addPanel("Traffic")
myWorkspace.addFreeform(
    "Events by page",
    item_id="variables/page",
    metrics=[{"id": "metrics/occurrences"}],
)
validation = myWorkspace.validateProject()
```

After reviewing the validation result, create the project:

```python
createdProject = myWorkspace.createProject()
```

Further edits can then be published with `myWorkspace.updateProject()`.

**NOTE**: API payloads exclude read-only fields returned by GET requests and local tags/shares. They use `dataId` and an owner `imsUserId` (or legacy numeric `id`). The full metadata is still preserved by `to_dict()`.\
To duplicate an existing project, remove the source project ID from the exported dictionary before loading it into a new instance and calling `createProject`.

For more information, see the [CJA Projects API](https://developer.adobe.com/cja-apis/docs/api#operation/projects_createProject), [Projects guide](https://developer.adobe.com/cja-apis/docs/endpoints/projects/), and [project structure](https://developer.adobe.com/cja-apis/docs/endpoints/projects/structure).
