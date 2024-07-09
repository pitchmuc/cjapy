# cjapy : RequestCreator class

The `cjapy` module provide a way for you to create request dictionary to CJA servers, it is done via the usage of the `RequestCreator`class.\
This class will provide you an instance that contains methods to modify your request definition.\
In this documentation, we will review the different methods available.

## RequestCreator instanciation

In order to generate an instance of the `RequestCreator`, once you have loaded the cjapy module, you can either directly call the class or pass an existing request definition.\

### Creating an empty request

```python
import cjapy
### creating an empty request 
myRequest = cjapy.RequestCreator()
```

The `myRequest` object will contain the following definition:

```python
{
        "globalFilters": [],
        "metricContainer": {
            "metrics": [],
            "metricFilters": [],
        },
        "dimension": "",
        "settings": {
            "countRepeatInstances": True,
            "limit": 20000,
            "page": 0,
            "nonesBehavior": "exclude-nones",
        },
        "statistics": {"functions": ["col-max", "col-min"]},
        "dataId": "",
    }
```

### Uploading a template request

```python
import cjapy, json
### loading your existing request, downloaded from CJA interface
with open('mySavedRequest.json','r') as f:
    saveRequest = json.load(f)
### passing the definition to the RequestCreator
myRequest = cjapy.RequestCreator(saveRequest)
```

In this case, `myRequest` will contain the definition that you have passed on the initiation of the RequestCreator instance.

## Methods availables on RequestCreator instance

Once your instance has been created, example: `myRequest`, several methods are available to you.\
We will review the different methods available via the object.

* `to_dict()`
  This method returns the current request definition, in a dictionary.

* `save()`
  This method saves the current request definition in a JSON file.
  Arguments:
  * filename : OPTIONAL : Name of the file. (default cjapy_request_<_timestamp_>.json)

* `setDimension()`
  Set the dimension to be used for reporting.
  Arguments:
  * dimension : REQUIRED : the dimension to build your report on

* `setDataViewId()`
  Set the dataView ID to be used for the reporting.
  Arguments:
  * dataViewId : REQUIRED : The Data View ID to be passed.

* `addMetric()`
  Add a metric to the Request.
  Arguments:
  * metricId : REQUIRED : The metric to add
  * attributionModel : OPTIONAL : The attribution model to use (e.g., "lastTouch", "firstTouch", "linear", "participation", "sameTouch", "uShaped", "jShaped", "reverseJShaped", "timeDecay", "positionBased", "algorithmic")
  * lookbackWindow : OPTIONAL : The lookback window (number of minutes, hours, days, weeks, months, quarters, "session", or "person"). Assumes 30 if not specified.
  * lookbackGranularity : OPTIONAL : The granularity of the lookback window (minute, hour, day, week, month, quarter). Defaults to "day".
  * **kwargs : Additional model-specific parameters. For "timeDecay" (assumes 1 week): halfLifeNumPeriods, halfLifeGranularity; for "positionBased": firstWeight, middleWeight, lastWeight.

  The `addMetric` method also supports various attribution models. For example, the `sameTouch` model is defined without a lookback window, while other models like `lastTouch` and `firstTouch` can have lookback windows and expiration settings. The `timeDecay` model allows specifying half-life periods and granularity, with defaults to 1 week if not provided.

  Examples:
  ```python
  # Adding a simple metric
  myRequest.addMetric("metrics/orders")

  # Adding a metric with an attribution model
  myRequest.addMetric("metrics/orders", attributionModel="lastTouch", lookbackWindow=30)

  # Adding a metric with a custom attribution model
  myRequest.addMetric(
      "metrics/orders",
      attributionModel="timeDecay",
      lookbackWindow=60,
      halfLifeNumPeriods=1,
      halfLifeGranularity="week"
  )

  # Adding a metric with position-based attribution model
  myRequest.addMetric(
      "metrics/orders",
      attributionModel="positionBased",
      lookbackWindow=30,
      firstWeight=30,
      middleWeight=20,
      lastWeight=50
  )

  # Adding a metric with sameTouch attribution model
  myRequest.addMetric("metrics/orders", attributionModel="sameTouch")

* `addGlobalFilter()`
  Add a global filter to the report.
  **NOTE** : You need to have a dateRange filter at least in the global report.
  Arguments:
  * filterId : REQUIRED : The filter to add to the global filter.\
        example:\
        "s293120jf3q9jf38301jd029f030128z482s" -> segment ID\
        "2020-01-01T00:00:00.000/2020-02-01T00:00:00.000" -> dateRange
        "dimension:::itemId" -> dimension value

* `removeGlobalFilter()`
  Remove a specific filter from the globalFilter list.
  You can use either the index of the list or the specific Id of the filter used.
  Arguments:
  * index : REQUIRED : index in the list return
  * filterId : REQUIRED : the id of the filter to be removed (ex: filterId, dateRange)

* `setNoneBehavior()`
  Set the behavior of the None values in that request.
  Arguments:
  * returnNones : OPTIONAL : True or False (True by default)

* `setRepeatInstance()`
  Specify if repeated instances should be counted.
  Arguments:
  * repeat : OPTIONAL : True or False (True by default)

* `setLimit()`
  Specific the number of element to retrieve. Default is 10.
  Arguments:
  * limit : OPTIONAL : number of elements to return

* `setSearch()`
  Set a search for specific value in the dimensions.
  Arguments:
  * itemIds : REQUIRED : list of value to search for.

* `removeSearch()`
  Remove the search attribute for the search capabilities.
  No arguments.

* `addMetricFilter()`
  Add a filter to a metric.
  Arguments:
  * metricId : REQUIRED : metric where the filter is added
  * filterId : REQUIRED : The filter to add.
    When breakdown, use the following format for the value "dimension:::itemId"
  * metricIndex : OPTIONAL : If used, set the filter to the metric located on that index.

* `removeMetricFilter()`
  remove a filter from a metric
  Arguments:
  * filterId : REQUIRED : The filter to add.
        when breakdown, use the following format for the value "dimension:::itemId"

* `updateDateRange()`
  Update the dateRange filter on the globalFilter list
  One of the 3 elements specified below is required.
  Arguments:
  * dateRange : OPTIONAL : string representing the new dateRange string, such as: 2020-01-01T00:00:00.000/2020-02-01T00:00:00.000
  * shiftingDays : OPTIONAL : An integer, if you want to add or remove days from the current dateRange provided. Apply to end and beginning of dateRange.
      So 2020-01-01T00:00:00.000/2020-02-01T00:00:00.000 with +2 will give 2020-01-03T00:00:00.000/2020-02-03T00:00:00.000
  * shiftingDaysEnd : : OPTIONAL : An integer, if you want to add or remove days from the last part of the current dateRange. Apply only to end of the dateRange.
      So 2020-01-01T00:00:00.000/2020-02-01T00:00:00.000 with +2 will give 2020-01-01T00:00:00.000/2020-02-03T00:00:00.000
  * shiftingDaysStart : OPTIONAL : An integer, if you want to add or remove days from the last first part of the current dateRange. Apply only to beginning of the dateRange.
      So 2020-01-01T00:00:00.000/2020-02-01T00:00:00.000 with +2 will give 2020-01-03T00:00:00.000/2020-02-01T00:00:00.000

## Instance attributes

At the moment, there are only limited attributes available on the instance of the `RequestCreator` class.

### dates

In order to help build the main date request for your global filter, I have prepared some predefined `dates` available to you.\
The different timeframe available through the `dates` attributes are the following:

* thisMonth : full month date
* untilToday : start of the month till yesterday midnight
* todayIncluded : start of the month, today included
* last30daysTillToday
* last30daysTodayIncluded
* last7daysTillToday
* last7daysTodayIncluded

### today

`today`attribute is a datetime object, with today timestamp.\
This can help you derive other dates if needed.

### search

`search` attribute is a boolean defining if search has been set for the dimension.
