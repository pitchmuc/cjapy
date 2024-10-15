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
mysegments = mycompany.getFilters()
```

Example of getDimensions usage:

```python
mydims = mycompany.getDimensions('rsid')
```

List of GET methods:

* getCurrentUser
  return the current user

* getUsers
  returns a list of all users with their IMS ID.

* getCalculatedMetrics
  Returns a dataframe or the list of calculated Metrics.
  Arguments
  * full : OPTIONAL : returns all possible attributs if set to True (False by default)
  * inclType : OPTIONAL : returns the type selected.Possible options are:
    * all (default)
    * shared
    * templates
    * unauthorized
    * deleted
    * internal
    * curatedItem
  * dataIds : OPTIONAL : Filters the result to calculated metrics tied to a specific Data View ID (comma-delimited)
  * ownerId : OPTIONAL : Filters the result by specific loginId.
  * limit : OPTIONAL : Number of results per request (Default 100)
  * filterByIds : OPTIONAL : Filter list to only include calculated metrics in the specified * list (comma-delimited),
  * favorite : OPTIONAL : If set to true, return only favorties calculated metrics. (default False)
  * approved : OPTIONAL : If set to true, returns only approved calculated metrics. (default False)
  * output : OPTIONAL : by default returns a "dataframe", can also return the list when set to "raw"

* getCalculatedMetricsFunctions
  Returns a list of calculated metrics functions.
  Arguments:
  * output : OPTIONAL : default to "raw", can return "dataframe".

* getCalculatedMetric
  Return a single calculated metrics based on its ID.
  Arguments:
  * calcId : REQUIRED : The calculated me

* getShares
  Returns the elements shared.
  Arguments:
  * userId : OPTIONAL : User ID to return details for.
  * inclType : OPTIONAL : Include additional shares not owned by the user
  * limit : OPTIONAL : number of result per request.
  * useCache: OPTIONAL : Caching the result (default True)

* getShare
  Returns a specific share element.
  Arguments:
  * shareId : REQUIRED : the element ID.
  * useCache : OPTIONAL : If caching the response (True by defaul

* getTags
  Return the tags for the company.
  Arguments:
  * limit : OPTIONAL : Number of result per request.

* getTag
  Return a single tag data by its ID.
  Arguments:
  * tagId : REQUIRED : The tag ID to retrieve.

* getComponentTags
  Return tags for a component based on its ID and type.
  Arguments:
  * componentId : REQUIRED : The component ID
  * componentType : REQUIRED : The component type.
      could be any of the following ; "segment" "dashboard" "bookmark" "calculatedMetric" "project" "dateRange" "metric" "dimension" "virtualReportSuite" "scheduledJob" "alert" "classificationSet" "dataView"

* getDateRanges
  Return daterange information in a list or in a dataframe
  Arguments:
  * limit : OPTIONAL : Number of result per request.
  * filterByIds : OPTIONAL : Filter list to only include date ranges in the specified list (comma-delimited list of IDs)
  * full : OPTIONAL : additional meta data information included.
  * includeType : OPTIONAL : Show daterange not owned by user (default "all")
      Possible values are "all", "shared", "templates"
  * output : OPTIONAL : Type of result returned.

* getDateRange
  Return a single dateRange definition.
  Argument:
  * dateRangeId : REQUIRED : date range ID to be returned

* getTopItems
  Get the top X items (based on paging restriction) for the specified dimension and dataId. Defaults to last 90 days.
  Arguments:
  * dataId : REQUIRED : Data Group or Data View to run the report against
  * dimension : REQUIRED : Dimension to run the report against. Example: "variables/page"
  * dateRange : OPTIONAL : Format: YYYY-MM-DD/YYYY-MM-DD (default 90 days)
  * startDate: OPTIONAL : Format: YYYY-MM-DD
  * endDate : OPTIONAL : Format: YYYY-MM-DD
  * limit : OPTIONAL : Number of results per request (default 100)
  * searchClause : OPTIONAL : General search string; wrap with single quotes. Example: 'PageABC'
  * searchAnd : OPTIONAL : Search terms that will be AND-ed together. Space delimited.
  * searchOr : OPTIONAL : Search terms that will be OR-ed together. Space delimited.
  * searchNot : OPTIONAL : Search terms that will be treated as NOT including. Space delimited.
  * searchPhrase : OPTIONAL : A full search phrase that will be searched for.
  * remoteLoad : OPTIONAL : tells to load the result in Oberon if possible (default True)
  * xml : OPTIONAL : returns the XML for debugging (default False)
  * noneValues : OPTIONAL : Controls None values to be included (default True)

* getDimensions
  Used to retrieve dimensions for a dataview
  Arguments:
  * dataviewId : REQUIRED : the Data View ID to retrieve data from.
  * full : OPTIONAL : To add additional elements (default False)
  * inclType : OPTIONAL : Possibility to add "hidden" values
  * output : OPTIONAL : Type of output selected, either "df" (default) or "raw"

* getDimension
  Return a specific dimension based on the dataview ID and dimension ID passed.
  Arguments:
  * dataviewId : REQUIRED : the Data View ID to retrieve data from.
  * dimensionId : REQUIRED : the dimension ID to return
  * full : OPTIONAL : To add additional elements (default True)

* getMetrics
  Used to retrieve metrics for a dataview
  Arguments:
  * dataviewId : REQUIRED : the Data View ID to retrieve data from.
  * full : OPTIONAL : To add additional elements (default False)
  * inclType : OPTIONAL : Possibility to add "hidden" values
  * output : OPTIONAL : Type of output selected, either "df" (default) or "raw"

* getMetric
  Return a specific metric based on the dataview ID and dimension ID passed.
  Arguments:
  * dataviewId : REQUIRED : the Data View ID to retrieve data from.
  * metricId : REQUIRED : the metric ID to return
  * full : OPTIONAL : To add additional elements (default True)

* getDataViews
  Returns the Data View configuration.
  Arguments:
  * limit : OPTIONAL : number of results per request (default 100)
  * full : OPTIONAL : define if all possible information are returned (default True).
  * output : OPTIONAL : Type of output selected, either "df" (default) or "raw"
  * parentDataGroupId : OPTIONAL : Filters data views by a single parentDataGroupId
  * externalIds : OPTIONAL : Comma-delimited list of external ids to limit the response with.
  * externalParentIds : OPTIONAL : Comma-delimited list of external parent ids to limit the * response with.
  * dataViewIds : OPTIONAL : Comma-delimited list of data view ids to limit the response with.
  * includeType : OPTIONAL : include additional DataViews not owned by user.(default "all")
  * cached : OPTIONAL : return cached results
  * verbose : OPTIONAL : add comments in the console.

* getDataView
  Returns a specific Data View configuration from Configuration ID.
  Arguments:
  * dataViewId : REQUIRED : The data view ID to retrieve.
  * full : OPTIONAL : getting extra information on the data view
  * save : OPTIONAL : save the response in JSON format

* getFilters
  Returns a list of filters used in CJA.
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

* getFilter
  Returns a single filter definition by its ID.
  Arguments:
  * filterId : REQUIRED : ID of the filter
  * full : OPTIONAL : Boolean to define additional elements

* getAuditLogs
  Get Audit Log when few filters are applied.
  All filters are applied with an AND condition.
  Arguments:
  * startDate : OPTIONAL : begin range date, format: YYYY-01-01T00:00:00-07 (required if endDate is used)
  * endDate : OPTIONAL : begin range date, format: YYYY-01-01T00:00:00-07 (required if startDate is used)
  * action : OPTIONAL : The type of action a user or system can make.
      Possible values : CREATE, EDIT, DELETE, LOGIN_FAILED, LOGIN_SUCCESSFUL, API_REQUEST
  * component : OPTIONAL :The type of component.
      Possible values : CALCULATED_METRIC, CONNECTION, DATA_GROUP, DATA_VIEW, DATE_RANGE, FILTER, MOBILE, PROJECT, REPORT, SCHEDULED_PROJECT
  * componentId : OPTIONAL : The id of the component.
  * userType : OPTIONAL : The type of user.
  * userId : OPTIONAL : The ID of the user.
  * userEmail : OPTIONAL : The email address of the user.
  * description : OPTIONAL : The description of the audit log.
  * pageSize : OPTIONAL : Number of results per page. If left null, the default size is 100.
  * n_results : OPTIONAL : Total number of results you want for that search. Default "inf" will return everything
  * output : OPTIONAL : DataFrame by default, can be "raw"

* getProjects
  Returns a list of project ID with their meta information attached to it.
  Arguments:
  * full : OPTIONAL : add all metadata attached to the project (default True)
  * includeType : OPTIONAL : Include additional segments not owned by user. ("all" or "shared")
  * filterByIds : OPTIONAL : Filter list to only include projects in the specified list (comma-delimited list of IDs)
  * ownerId : OPTIONAL : Filter list to only include projects owned by the specified imsUserId
  * limit : OPTIONAL : Number of results per request
  * save : OPTIONAL : if you want to save the result
  * output : OPTIONAL : the type of output to return "df" or "raw"

* getProject
  Return a specific project with its definition
  Arguments:
  * projectId : REQUIRED : a project ID to return

* getAnnotation
  Return a specific annotation definition.
  Arguments:
  * annotationId : REQUIRED : The annotation ID

* getAnnotations
  Returns a list of the available annotations 
  Arguments:
  * full : OPTIONAL : If set to True (default), returned all available information of the annotation.
  * includeType : OPTIONAL : use to return only "shared" or "all"(default) annotation available.
  * limit : OPTIONAL : number of result per page (default 1000)
  * page : OPTIONAL : page used for pagination

* getConnections
  Returns a list of the connections for this company id. Returns either a list of a dataframe.
  Arguments:
  * limit : OPTIONAL : number of results per request (default 100)
  * full : OPTIONAL : define if all possible information are returned (default True).
  * output : OPTIONAL : Type of output selected, either "df" (default) or "raw"

* getConnection
  Return a connection detail based on its ID (without prefix).
  Arguments:
  * connectionId : REQUIRED : the connection ID (without prefix)

* getAssetCount
  Get the assets own by a specific user.
  Arguments:
  * imsUserId : REQUIRED : The user ID owning the assets.


## Create methods

The CJA API  provides some endpoint to create elements.
Here is the list of the possible create options.

* createTags: Create tags for the company, attached to components.
  Arguments:
  * data : REQUIRED : list of elements to passed.
      Example [
          {
              "id": 0,
              "name": "string",
              "description": "string",
              "components": [
              null
              ]
          }
      ]

* createDataView
  Create and stores the given Data View in the db.
  Arguments:
  * data : REQUIRED : The dictionary or json file that holds the definition for the dataview to be created.

* createFilter
  Arguments:
  * data : REQUIRED : Dictionary or JSON file to create a filter
  possible kwargs:
  * encoding : if you pass a JSON file, you can change the encoding to read it.

* createCalculatedMetric: Create a calculated metrics based on the dictionary
  Arguments:
  * data : REQUIRED : dictionary that will set the creation.

* Create a project based on the definition provided in the argument.
  Argument:
  * projectDefinition : REQUIRED : the project dictionary defining the creation.

* createDateRange
  Create a single dateRange with the dictionary passed
  Argument:
  * dateRangeData : REQUIRED : date range ID to be created

* createAnnotation
  Create an Annotation.
  Arguments:
  * name : REQUIRED : Name of the annotation
  * dateRange : REQUIRED : Date range of the annotation to be used. 
      Example: 2022-04-19T00:00:00/2022-04-19T23:59:59
  * dataViewId : REQUIRED : Data View ID 
  * metricIds : OPTIONAL : List of metrics ID to be annotated
  * filterIds : OPTIONAL : List of filters ID to apply for annotation for context.
  * dimensionObj : OPTIONAL : List of dimensions object specification:
      {
          componentType: "dimension"
          dimensionType: "string"
          id: "variables/product"
          operator: "streq"
          terms: ["unknown"]
      }
  * applyToAllReports : OPTIONAL : If the annotation apply to all ReportSuites.
possible kwargs:
  * colors: Color to be used, examples: "STANDARD1"
  * shares: List of userId for sharing the annotation
  * tags: List of tagIds to be applied
  * favorite: boolean to set the annotation as favorite (false by default)
  * approved: boolean to set the annotation as approved (false by default)

## DELETE methods

There is a possibility to delete some elements with the Adobe Analytics API 2.0. Please find below the different options that you can delete.

* deleteFilter: Delete a filter based on its ID.
  Arguments:
  * filterId : REQUIRED : Filter ID to be deleted

* deleteDataView: Delete a data view by its ID.
  Arguments:
  * dataViewId : REQUIRED : the data view ID to be deleted

* deleteTags: Delete a calculated metrics based on its ID.
  Removes all tags from the passed componentIds.
  Note that currently this is done in a single DB query, so there is a single combined response for the entire operation.
  Arguments:
  * componentIds : REQUIRED : comma separated list of component ids to remove tags.
  * componentType : REQUIRED : The component type to operate on.
    could be any of the following ; "segment" "dashboard" "bookmark" "calculatedMetric" "project" "dateRange" "metric" "dimension" "virtualReportSuite" "scheduledJob" "alert" "classificationSet" "dataView"

* deleteShare: Delete the shares of an element.
  Arguments:
  * shareId : REQUIRED : the element ID to be deleted.

* deleteCalculateMetrics: Delete a calculated metrics based on its ID.
  Arguments:
  * calcId : REQUIRED : The calculated metrics ID that will be deleted

* Delete a project by its ID.
  Arguments:
  * projectId : REQUIRED : ID of the project to delete.

* deleteDateRange
  Delete a single dateRange definition.
  Argument:
  * dateRangeId : REQUIRED : date range ID to be deleted

* deleteAnnotation
  Delete a specific annotation definition.
  Arguments:
  * annotationId : REQUIRED : The annotation ID to be deleted

## UPDATE methods

CJA API provides some method PUT and PATCH that are available to update some component of the CJA.\
On each method docstring, I tried to tell if it is a PUT or a PATCH method.

* updateCalculatedMetrics: Will overwrite the calculated metrics object with the new object   (PUT method)
  Arguments:
  * calcId : REQUIRED : The calculated metric ID to be updated
  * data : REQUIRED : The dictionary that will overwrite.

* updateShares: Create one/many shares for one/many components at once. This is a PUT request.
  For each component object in the passed list, the given shares will replace the current set of shares for each component.
  Arguments:
  * data : REQUIRED : list of dictionary containing the component to share.
      Example
      ```py
      [
        {
          "componentType": "string",
          "componentId": "string",
          "shares": [
          {
              "shareToId": 0,
              "shareToImsId": "string",
              "shareToType": "string",
              "accessLevel": "string"
          }
          ]
        }
      ]
      ```
  * useCache : OPTIONAL : Boolean to use caching. Default is True.

* updateTags: This endpoint allows many tags at once to be created/deleted. PUT method.
  Any tags passed to this endpoint will become the only tags for that componentId (all other tags will be removed).
  Arguments:
  * data : REQUIRED : List of tags and component to be tagged.
    Example 
    ```py
    [
      {
        "componentType": "string",
        "componentId": "string",
        "tags": [
            {
              "id": 0,
              "name": "string",
              "description": "string",
              "components": [
              null
              ]
            }
        ]
      }
    ]
    ```

* updateDataView: Update the Data View definition (PUT method)
  Arguments:
  * dataViewId : REQUIRED : the data view ID to be updated
  * data : REQUIRED : The dictionary or JSON file that holds the definition for the dataview to be updated
  possible kwargs:
  * encoding : if you pass a JSON file, you can change the encoding to read it.

* updateFilter: Update a filter based on the filter ID.
  Arguments:
  * filterId : REQUIRED : Filter ID to be updated
  * data : REQUIRED : Dictionary or JSON file to update the filter
  possible kwargs:
  * encoding : if you pass a JSON file, you can change the encoding to read it.

* updateProject : Update a project based on the definition provided in the argument. (PUT Method)
  Arguments:
  * projectId : REQUIRED : ID of the project to update.
  * projectDefinition : REQUIRED : the project dictionary defining the creation.

* updateDateRange
  Update a single dateRange with the new object
  Arguments:
  * dateRangeId : REQUIRED : date range ID to be updated
  * data : REQUIRED : dictionary holding the new definition

* updateAnnotation
  Update an annotation based on its ID. PUT method.
  Arguments:
  * annotationId : REQUIRED : The annotation ID to be updated
  * annotationObj : REQUIRED : The object to replace the annotation.

## Other methods

* validateCalculatedMetric: Validate a calculated metrics definition dictionary.
  Arguments:
  * data : REQUIRED : dictionary that will set the creation.

* searchShares: Search for multiple shares on component based on the data passed.
  Arguments:
  * data : REQUIRED : dictionary specifying the search.
    example: 
    ```py
    {
        "componentType": "string",
        "componentIds": [
            "string"
        ],
        "dataId": "string"
    }
    ```
  * full : OPTIONAL : add additional data in the results.(Default False)
  * limit : OPTIONAL : number of result per page (10 per default)

* validateDataView: Validate the dictionary for the creation of a data view.
  Argument:
  * data : REQUIRED : The dictionary or json file that holds the definition for the dataview to be created.

* copyDataView: Copy the setting of a specific data view.
  Arguments:
  * dataViewId : REQUIRED : Data View ID to copy the setting on

* validateFilter: Validate the syntax for filter creation.
  Arguments:
  * data : REQUIRED : Dictionary or JSON file to create a filter
  possible kwargs:
  * encoding : if you pass a JSON file, you can change the encoding to read it.

* searchAuditLogs: Get Audit Log when several filters are applied. You can define the different type of operator and connector to use.
  Operators: EQUALS, CONTAINS, NOT_EQUALS, IN
  Connectors: AND, OR
  **Note**: there is a sample for creating a filterMessage available as attribute of your instance: `SAMPLE_FILTERMESSAGE_LOGS`
  That may help you creating the filter.
  Arguments:
  * filterMessage : REQUIRED : A dictionary of the search to the Audit Log.

* validateProject: Validates a Project definition.
  Arguments:
  * projectDefinition : REQUIRED : the project dictionary defining the creation.

* transferAssets: Transfer the assets to a specific user.
  Arguments:
  * imsUserId : REQUIRED : The user ID to transfer the assets to.
  * assets : REQUIRED : The list of assets to be transfered.
    Example:
    ```py
      [
        {
          "componentType": "string",
          "componentIds": [
          "string"
          ]
      }
      ]
    ```

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

Example:

```python
import cjapy
import json

cjapy.importConfigFile('myConfig.json')

## Possibility 1 : load a request definition delivered by CJA interface debugger.
with open('myRequest.json','r') as f:
    myRequest = json.load(f)

myReport = cjapy.getReport(myRequest)

## Possibility 2 : Create a request from scratch via the Request Creator
myRequest = cjapy.RequestCreator()
myRequest.setDimension('variables/...')
# ... other methods to build it
requestDef = myRequest.to_dict()

myReport = cjapy.getReport(requestDef)
```

**Handling Throttle** : The throttle limit of 12 requests per 6 seconds or 120 requests per minute is handle automatically. It automatically pause the requests for 50 seconds when the limit is reached.

### Get getMultidimensionalReport (BETA)

The `getMultidimensionalReport` is a beta feature of the `cjapy` module.\
This method, as its name suggests, enable you to realize automatic breakdown report in your CJA environment.\
The back end of that capability is leveraging the `getReport` and wrapping it with a logic.\
It returns a  `Workspace` instance.\
No reference to metric filters are being returned in the result as it depends on the iteration of the loop.

The following arguments are possible with this method:

* dimensions : REQUIRED : list of the dimension to breakdown. In the order of the breakdown.
* dimensionLimit : REQUIRED : the number of results to return for each breakdown.
    dictionnary like this: {'dimension1':5,'dimension2':10}
    You can ask to return everything from a dimension by using the 'inf' method
* metrics : REQUIRED : list of metrics to return
* dataViewId : REQUIRED : The dataView Id to use for your report.
* globalFilters : REQUIRED : list of filtersID to be used.
    example : ["filterId1","2020-01-01T00:00:00.000/2020-02-01T00:00:00.000"]
* metricFilters : OPTIONAL : dictionary of the filter you want to apply to the metrics.
    dictionnary like this : {"metric1":"segId1","metric":"segId2"}
* countRepeatInstances : OPTIONAL : set to count repeatInstances values (or not). True by default.
* returnNones : OPTIONAL : Set the behavior of the None values in that request. (True by default)


## getPersonProfiles

The `getPersonProfiles` method retrieves a dataset where each row represents a person profile. This is particularly useful for extracting feature metrics and target metrics for supervised learning applications or customer segmentation analysis.

### Arguments:
- `dataviewId`: **REQUIRED**. The Data View ID to use for your report.
- `personId`: **OPTIONAL**. The dimension to use as your person ID. Defaults to `variables/adobe_identitynamespace_personid`.
- `featureMetrics`: **REQUIRED**. A list of metrics to include in the customer profiles.
- `targetMetric`: **OPTIONAL**. A target metric for supervised learning algorithms.
- `binaryTargetMetric`: **OPTIONAL**. If set to `True`, sets the target metric to 1 if the metric sum for a person is greater than 0, otherwise sets it to 0.
- `startDate`: **OPTIONAL**. The start date for the report in 'YYYY-MM-DD' format or as a datetime object. Defaults to 90 days ago.
- `endDate`: **OPTIONAL**. The end date for the report in 'YYYY-MM-DD' format or as a datetime object. Defaults to today.
- `sampleSize`: **OPTIONAL**. The number of sampled person profiles to return. Defaults to 50,000. If the sample size exceeds the total population, all profiles are returned.
- `sampleSeed`: **OPTIONAL**. A seed value for random sampling of person profiles. Defaults to 0.
- `fullPersonHistoryOnly`: **OPTIONAL**. If set to `True`, filters the sample to only people whose entire history is present in the date range. Defaults to `False`.
- `removeSingleEventPeople`: **OPTIONAL**. If set to `True`, removes people that had only a single event in the date range.
- `filterId`: **OPTIONAL**. The segment ID to filter the report with.

### Returns:
A `pandas.DataFrame` containing the person profile data.

### Example usage:

```python
# Assuming `cja` is an instance of the CJA class
feature_metrics = ["metric1", "metric2", "metric3"]
df_profiles = cja.getPersonProfiles(
    dataviewId="your_data_view_id",
    featureMetrics=feature_metrics,
    targetMetric="target_metric",
    startDate="2023-01-01",
    endDate="2023-03-31",
    sampleSize=10000,
    binaryTargetMetric=True
)
print(df_profiles.head())
```

[Back to README](../README.md)
