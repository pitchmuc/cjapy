[Back to README](../README.md)

# CJA class

Most of the methods that you can use from the `cjapy` are stored within the `CJA` class instances.\
This documentation will provide an overview on the different methods available in that class.

You can always apply the *_help()_* function to any of the method that are available in your instance.\
Normaly a docstring is available to explain the usage of the parameters.

In the following part, I will explain the GET, DELETE and CREATE methods that are available on your instance of this class.\
At the end, we will focus briefly on the `getReport` method available.

## The GET methods

There are several get methods available in the API.

* getFilters : Get the list of filters.Returns a data frame or a JSON list.
  Arguments:
  * limit : OPTIONAL : number of result per request (default 100)
  * full : OPTIONAL : add additional information to the filters
  * output : OPTIONAL : Type of output selected, either "df" (default) or "raw"
  * includeType : OPTIONAL : Include additional segments not owned by user.(default all)
    possible values are "shared" "templates" "deleted" "internal"
  * name : OPTIONAL : Filter list to only include filters that contains the Name
  * dataIds : OPTIONAL : Filter list to only include filters tied to the specified data group ID list (comma-delimited)
  * ownerId : OPTIONAL : Filter by a specific owner ID.
  * filterByIds : OPTIONAL : Filters by filter ID (comma-separated list)
  * cached : OPTIONAL : return cached results
  * toBeUsedInRsid : OPTIONAL : The report suite where the filters is intended to be used. This report suite will be used to determine things like compatibility and permissions.

Example of getFilters usage:

```python
mysegments = mycompany.getSegments(extended_info=True,save=True)
```

Example of getDimensions usage:

```python
mydims = mycompany.getDimensions('rsid')
```

## Create methods

The CJA API  provides some endpoint to create elements.
Here is the list of the possible create options.

* createVirtualReportSuite: Create a new virtual report suite based on the information provided.
  Arguments:
  * name : REQUIRED : name of the virtual reportSuite
  * parentRsid : REQUIRED : Parent reportSuite ID for the VRS
  * segmentLists : REQUIRED : list of segment id to be applied on the ReportSuite.
  * dataSchema : REQUIRED : Type of schema used for the VRSID. (default : "Cache")
  * data_dict : OPTIONAL : you can pass directly the dictionary.
  In this case, you dictionary should looks like this:

  ```python
  data_dict = {
    'name' : 'xxxx',
    'parentRsid':'',
    'segmentLists':'',
    'dataSchema':'Cache',
  }
  ```

* createSegment: This method create segment based on the information provided in the dictionary passed as parameter.
  Arguments:
  * segmentJSON : REQUIRED : the dictionary that represents the JSON statement for the segment.
  The segmentJSON is referenced on this [Swagger reference](https://adobedocs.github.io/analytics-2.0-apis/#/segments/segments_createSegment)

* createCalculatedMetrics: This method create a calculated metrics within your Login Company with the provided dictionary.
  Arguments:
  * metricJSON : REQUIRED : Calculated Metrics information to create. Required :  name, definition, rsid
    more information can be found on the [Swagger refrence](https://adobedocs.github.io/analytics-2.0-apis/#/calculatedmetrics/calculatedmetrics_createCalculatedMetric)
  
* createCalculatedMetricValidate: Validate a calculated metrics definition or object passed.
  Arguments:
  * metricJSON : REQUIRED : Calculated Metrics information to create. (Required: name, definition, rsid)
      More information can be found at this address <https://adobedocs.github.io/analytics-2.0-apis/#/calculatedmetrics/calculatedmetrics_createCalculatedMetric>

* createTags : This method creates a tag and associate it with a component.
  Arguments:
  * data : REQUIRED : The list of the tag to be created with their component relation.
  It looks like the following:

  ```JSON
  [
    {
        "id": 0,
        "name": "string",
        "description": "string",
        "components": [
        {
            "componentType": "string",
            "componentId": "string",
            "tags": [
            "Unknown Type: Tag"
            ]
        }
        ]
    }
  ]
  ```

## DELETE methods

There is a possibility to delete some elements with the Adobe Analytics API 2.0. Please find below the different options that you can delete.

* deleteVirtualReportSuite: delete a Virtual reportSuite based on its ID.
  Arguments:
  * vrsid : REQUIRED : The id of the virtual reportSuite to delete.

* deleteSegment: delete a segment based on the ID.
  Arguments:
  * segmentID : the ID of the segment to be deleted.

* deleteCalculatedMetrics: Delete a calculated metrics based on its ID.
  Arguments:
  * calcID : REQUIRED : Calculated Metrics ID to be deleted

* deleteTags: Delete all tags from the component Type and the component ids specified.
  Arguments:
  * componentIds : REQUIRED : the Comma-separated list of componentIds to operate on.
  * componentType : REQUIRED : The component type to operate on.\
    Available values : segment, dashboard, bookmark, calculatedMetric, project, dateRange, metric, dimension, virtualReportSuite, scheduledJob, alert, classificationSet

* deleteTag : Delete a Tag based on its id.
  Arguments:
  * tagId : REQUIRED : The tag ID to be deleted.

* deleteProject : Delete a Project basede on its id.
  Arguments:
  * projectId : REQUIRED : The project ID to be deleted.

### Get report

The `getReport` from CJA is actually a POST method.\
It will push the request that you have provided to the method to the CJA server and return the response, by default in the form of a `Workspace` class instance.\

First of all, you need to understand that this API is a replication of the Workspace interface.
There is no additional features or way to bypass the limitation of Analytics Workspace by using this API.

Some limitations:

* A limit of 120 requests per minute is set, on top of a limit threshold of 12 requests for 6 seconds.\
  Because of that limit, I didn't parallelize the report requests, as the report as the threshold can be hit quite rapidly.\
  Therefore, requesting large amount of data is not the use-case for the CJA API. It would infer a important waiting time.
* There is no automatic breakdown for dimensions. As for the Workspace reporting, you can only request one dimension at a time.
* CJA reporting server usually allows 5 reports to be processed at the same time for your organization.\
  The CJA API will compete with the others users of your organization, so be careful on its (extensive) usage.

Before going with examples, I will explain the method and its arguments:

* getReport : Retrieve data from a JSON request.
              Returns an dictionary of data or a `Workspace` instance containing the data in the dataframe attribute.
  Arguments:
  * request : REQUIRED : either a dictionary of a JSON file that contains the request information.
  * limit : OPTIONAL : number of results per request (default 1000)
  * n_results : OPTIONAL : total number of results returns. Use "inf" to return everything (default "inf")
  * allowRemoteLoad : OPTIONAL : Controls if Oberon should remote load data. Default behavior is true with fallback to false if remote data does not exist
  * useCache : OPTIONAL : Use caching for faster requests (Do not do any report caching)
  * useResultsCache : OPTIONAL : Use results caching for faster reporting times (This is a pass through to Oberon which manages the Cache)
  * includeOberonXml : OPTIONAL : Controls if Oberon XML should be returned in the response - DEBUG ONLY
  * includePredictiveObjects : OPTIONAL : Controls if platform Predictive Objects should be returned in the response. Only available when using Anomaly Detection or Forecasting- DEBUG ONLY
  * returnsNone : OPTIONAL: Overwritte the request setting to return None values.
  * countRepeatInstance : OPTIONAL: Overwritte the request setting to count repeatInstances values.
  * ignoreZeroes : OPTIONAL : Ignore zeros in the results
  * dataViewId : OPTIONAL : Overwrite the data View ID used for report. Only works if the same components are presents.
  * resolveColumns: OPTIONAL : automatically resolve columns from ID to name for calculated metrics & segments. Default True. (works on returnClass only)
  * save : OPTIONAL : If you want to save the data (in JSON or CSV, depending the class is used or not)
  * returnClass : OPTIONAL : return the class building dataframe and better comprehension of data. (default yes)

I am recommending to try returning the `Workspace` class as often as possible (default method).
This will provide the more intelligible report for you.

You can have more information on the `Workspace` instance on that documentation: [cjapy Workspace documentation](./workspace.md)

**Handling Throttle** : The throttle limit of 12 requests per 6 seconds or 120 requests per minute is handle automatically. It automatically pause the requests for 50 seconds when the limit is reached.

[Back to README](../README.md)
