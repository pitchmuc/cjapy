from copy import deepcopy
import datetime
import json
from time import time
from typeing import Union

class RequestCreator:
    """
    A class to help build a request for CJA API getReport
    """

    template = {
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
            "sampling": None,
            "samplingUpSample": None
        },
        "statistics": {"functions": ["col-max", "col-min"]},
        "dataId": "",
        "identityOverrides": [],
        "capacityMetadata":{
            "associations": [
                {
                    "name": "applicationName",
                    "value": "cjapy Python Library"
                }
            ]
        }
    }

    def __init__(self, request: dict = None) -> None:
        """
        Instanciate the constructor.
        Arguments:
            request : OPTIONAL : overwrite the template with the definition provided.
        """
        if request is not None:
            if '.json' in request and type(request) == str:
                with open(request,'r') as f:
                    request = json.load(f)
        self.__request = deepcopy(request) or deepcopy(self.template)
        self.__metricCount = len(self.__request["metricContainer"]["metrics"])
        self.__metricFilterCount = len(
            self.__request["metricContainer"].get("metricFilters", [])
        )
        self.__globalFiltersCount = len(self.__request["globalFilters"])
        self.search = False ## defining if search is being used.
        if 'search' in self.__request.keys():
            self.search = True
        ### Preparing some time statement.
        today = datetime.datetime.now()
        today_date_iso = today.isoformat().split("T")[0]
        ## should give '20XX-XX-XX'
        tomorrow_date_iso = (
            (today + datetime.timedelta(days=1)).isoformat().split("T")[0]
        )
        time_start = "T00:00:00.000"
        time_end = "T23:59:59.999"
        startToday_iso = today_date_iso + time_start
        endToday_iso = today_date_iso + time_end
        startMonth_iso = f"{today_date_iso[:-2]}01{time_start}"
        tomorrow_iso = tomorrow_date_iso + time_start
        next_month = today.replace(day=28) + datetime.timedelta(days=4)
        last_day_month = next_month - datetime.timedelta(days=next_month.day)
        last_day_month_date_iso = last_day_month.isoformat().split("T")[0]
        last_day_month_iso = last_day_month_date_iso + time_end
        thirty_days_prior_date_iso = (
            (today - datetime.timedelta(days=30)).isoformat().split("T")[0]
        )
        thirty_days_prior_iso = thirty_days_prior_date_iso + time_start
        seven_days_prior_iso_date = (
            (today - datetime.timedelta(days=7)).isoformat().split("T")[0]
        )
        seven_days_prior_iso = seven_days_prior_iso_date + time_start
        ### assigning predefined dates:
        self.dates = {
            "thisMonth": f"{startMonth_iso}/{last_day_month_iso}",
            "untilToday": f"{startMonth_iso}/{startToday_iso}",
            "todayIncluded": f"{startMonth_iso}/{endToday_iso}",
            "last30daysTillToday": f"{thirty_days_prior_iso}/{startToday_iso}",
            "last30daysTodayIncluded": f"{thirty_days_prior_iso}/{tomorrow_iso}",
            "last7daysTillToday": f"{seven_days_prior_iso}/{startToday_iso}",
            "last7daysTodayIncluded": f"{seven_days_prior_iso}/{endToday_iso}",
        }
        self.today = today

    def __repr__(self):
        return json.dumps(self.__request, indent=4)

    def __str__(self):
        return json.dumps(self.__request, indent=4)

    def addMetric(
        self,
        metricId: str = None,
        attributionModel: str = None,
        lookbackWindow: Union[int, str] = 30,
        lookbackGranularity: str = "day",
        **kwargs
    ) -> None:
        """
        Add a metric to the template.
        Arguments:
            metricId : REQUIRED : The metric to add
            attributionModel : OPTIONAL : The attribution model to use (e.g., "lastTouch", "firstTouch", "linear", "participation", "sameTouch", "uShaped", "jShaped", "reverseJShaped", "timeDecay", "positionBased", "algorithmic")
            lookbackWindow : OPTIONAL : The lookback window (number of minutes, hours, days, weeks, months, quarters, "session", or "person"). Assumes 30 if not specified.
            lookbackGranularity : OPTIONAL : The granularity of the lookback window (minute, hour, day, week, month, quarter). Defaults to "day".
            **kwargs : Additional model-specific parameters. For "timeDecay" (assumes 1 week): halfLifeNumPeriods, halfLifeGranularity, for "positionBased": firstWeight, middleWeight, lastWeight.
        """
        if metricId is None:
            raise ValueError("Require a metric ID")
        
        if attributionModel and attributionModel not in ["lastTouch", "firstTouch", "linear", "participation", "sameTouch", "uShaped", "jShaped", "reverseJShaped", "timeDecay", "positionBased", "algorithmic"]:
            raise ValueError("Invalid attribution model")
              
        if attributionModel and lookbackGranularity not in ["minute", "hour", "day", "week", "month", "quarter"]:
            raise ValueError("Invalid lookbackGranularity. Valid values are: 'minute', 'hour', 'day', 'week', 'month', 'quarter'")
        
        columnId = self.__metricCount
        addMetric = {"columnId": str(columnId), "id": metricId}
        if columnId == 0:
            addMetric["sort"] = "desc"

        if attributionModel:
            # Handle sameTouch separately
            if attributionModel == "sameTouch":
                if lookbackWindow is not None or kwargs:
                    raise ValueError("sameTouch does not accept a lookbackWindow, lookbackGranularity, or other parameters")
                allocationModel = {
                    "func": "allocation-instance"
                }
            else:
                allocationModel = {
                    "func": f"allocation-{attributionModel}"
                }

            # Validate lookback window
            if lookbackWindow is not None:
                if isinstance(lookbackWindow, int):
                    if lookbackWindow <= 0:
                        raise ValueError("lookbackWindow must be positive")

                    # Default lookback granularity to days if not specified
                    lookbackGranularity = kwargs.get('lookbackGranularity', lookbackGranularity)

                    max_lookback = {
                        'minute': 129600,
                        'hour': 2160,
                        'day': 90,
                        'week': 12,
                        'month': 3,
                        'quarter': 1
                    }.get(lookbackGranularity, 90)

                    if lookbackWindow > max_lookback:
                        raise ValueError(f"lookbackWindow of {lookbackWindow} exceeds maximum for {lookbackGranularity} granularity")

                    if attributionModel not in ["lastTouch", "firstTouch"] or lookbackWindow != "session":
                        allocationModel["lookbackExpiration"] = {
                            "func": "allocation-lookbackPeriod",
                            "granularity": lookbackGranularity,
                            "numPeriods": lookbackWindow
                        }

                        addMetric["lookback"] = {
                            "func": "min-months",
                            "granularity": lookbackGranularity,
                            "numPeriods": lookbackWindow
                        }

                    if attributionModel in ["lastTouch", "firstTouch"]:
                        allocationModel["expiration"] = {
                            "context": "visitors",
                            "func": "allocation-container"
                        }
                    else:
                        allocationModel["context"] = "visitors"
                    
                elif lookbackWindow == "session":
                    if attributionModel in ["lastTouch", "firstTouch"]:
                        allocationModel["expiration"] = {
                            "context": "sessions",
                            "func": "allocation-container"
                        }
                    else:
                        allocationModel["context"] = "sessions"
                elif lookbackWindow == "person":
                    if attributionModel not in ["lastTouch", "firstTouch"]:
                        allocationModel["context"] = "visitors"
                else:
                    raise ValueError("lookbackWindow must be a positive integer or 'session' or 'person'")

            if attributionModel in ["lastTouch", "firstTouch"]:
                allocationModel["expiration"] = {
                    "context": allocationModel.get("expiration", {}).get("context", "visitors"),
                    "func": "allocation-container"
                }

            if attributionModel == "timeDecay":
                halfLifeNumPeriods = kwargs.get("halfLifeNumPeriods", 1)
                halfLifeGranularity = kwargs.get("halfLifeGranularity", "week")
                if halfLifeNumPeriods is None or halfLifeGranularity not in ["minute", "hour", "day", "week", "month"]:
                    raise ValueError("For 'timeDecay', both 'halfLifeNumPeriods' and 'halfLifeGranularity' are required and granularity must be 'minute', 'hour', 'day', 'week', or 'month'")
                allocationModel["halfLifeGranularity"] = halfLifeGranularity
                allocationModel["halfLifeNumPeriods"] = halfLifeNumPeriods
            
            if attributionModel == "positionBased":
                firstWeight = kwargs.get("firstWeight")
                middleWeight = kwargs.get("middleWeight")
                lastWeight = kwargs.get("lastWeight")
                if firstWeight is None or middleWeight is None or lastWeight is None:
                    raise ValueError("For 'positionBased', 'firstWeight', 'middleWeight', and 'lastWeight' are required")
                allocationModel["firstWeight"] = firstWeight
                allocationModel["middleWeight"] = middleWeight
                allocationModel["lastWeight"] = lastWeight

            addMetric["allocationModel"] = allocationModel
        
        self.__request["metricContainer"]["metrics"].append(addMetric)
        self.__metricCount += 1

    def getMetrics(self) -> list:
        """
        return a list of the metrics used
        """
        return [metric["id"] for metric in self.__request["metricContainer"]["metrics"]]

    def addMetricFilter(
        self, metricId: str = None, filterId: str = None, metricIndex: int = None
    ) -> None:
        """
        Add a filter to a metric.
        Arguments:
            metricId : REQUIRED : metric where the filter is added
            filterId : REQUIRED : The filter to add.
                when breakdown, use the following format for the value "dimension:::itemId"
            metricIndex : OPTIONAL : If used, set the filter to the metric located on that index.
        """
        if metricId is None:
            raise ValueError("Require a metric ID")
        if filterId is None:
            raise ValueError("Require a filter ID")
        filterIdCount = self.__metricFilterCount
        if filterId.startswith("s") and "@AdobeOrg" in filterId:
            filterType = "segment"
            filter = {
                "id": str(filterIdCount),
                "type": filterType,
                "segmentId": filterId,
            }
        elif filterId.startswith("20") and "/20" in filterId:
            filterType = "dateRange"
            filter = {
                "id": str(filterIdCount),
                "type": filterType,
                "dateRange": filterId,
            }
        elif ":::" in filterId:
            filterType = "breakdown"
            dimension, itemId = filterId.split(":::")
            filter = {
                "id": str(filterIdCount),
                "type": filterType,
                "dimension": dimension,
                "itemId": itemId,
            }
        else:  ### case when it is predefined segments like "All_Visits"
            filterType = "segment"
            filter = {
                "id": str(filterIdCount),
                "type": filterType,
                "segmentId": filterId,
            }
        if filterIdCount == 0:
            self.__request["metricContainer"]["metricFilters"] = [filter]
        else:
            self.__request["metricContainer"]["metricFilters"].append(filter)
        ### adding filter to the metric
        if metricIndex is None:
            for metric in self.__request["metricContainer"]["metrics"]:
                if metric["id"] == metricId:
                    if "filters" in metric.keys():
                        metric["filters"].append(str(filterIdCount))
                    else:
                        metric["filters"] = [str(filterIdCount)]
        else:
            metric = self.__request["metricContainer"]["metrics"][metricIndex]
            if "filters" in metric.keys():
                metric["filters"].append(str(filterIdCount))
            else:
                metric["filters"] = [str(filterIdCount)]
        ### incrementing the filter counter
        self.__metricFilterCount += 1

    def removeMetricFilter(self, filterId: str = None) -> None:
        """
        remove a filter from a metric
        Arguments:
            filterId : REQUIRED : The filter to add.
                when breakdown, use the following format for the value "dimension:::itemId"
        """
        found = False  ## flag
        if filterId is None:
            raise ValueError("Require a filter ID")
        if ":::" in filterId:
            filterId = filterId.split(":::")[1]
        list_index = []
        for metricFilter in self.__request["metricContainer"]["metricFilters"]:
            if filterId in str(metricFilter):
                list_index.append(metricFilter["id"])
                found = True
        ## decrementing the filter counter
        if found:
            for metricFilterId in reversed(list_index):
                del self.__request["metricContainer"]["metricFilters"][
                    int(metricFilterId)
                ]
                for metric in self.__request["metricContainer"]["metrics"]:
                    if metricFilterId in metric.get("filters", []):
                        metric["filters"].remove(metricFilterId)
                self.__metricFilterCount -= 1

    def setLimit(self, limit: int = 100) -> None:
        """
        Specific the number of element to retrieve. Default is 10.
        Arguments:
            limit : OPTIONAL : number of elements to return
        """
        self.__request["settings"]["limit"] = limit

    def setSearch(self,itemIds:list=None,clause:str=None,reset:bool=True)-> None:
        """
        Set the items ID search in the specified dimension
        Arguments :
            itemIds : OPTIONAL : The list of itemId to be searched in the dimension
            clause : OPTIONAL : If you want to set a specific clause such as:
                "( CONTAINS 'Python' ) AND ( CONTAINS 'Platform' )"
                "( CONTAINS 'Python' ) OR ( CONTAINS 'Platform' )"
                "( MATCH 'Python' )" : Equals
                "( BEGINS-WITH 'Python' )"
                "( NOT CONTAINS 'Python' )"
            reset : OPTIONAL : automatically reset the search from your request
        """
        if reset:
            self.__request['search']={}
        if itemIds is not None:
            self.__request["search"]["itemIds"] = itemIds
        elif clause is not None:
            self.__request["search"]["clause"] = clause
        self.search = True

    # def addDimensions(self,dimensionIds:list=None)->None:
    #     """
    #     In case you want to pass a list of dimensions to the report API.
    #     Arguments:
    #         dimensionIds : REQUIRED : The list of dimensions IDs you want to use
    #     """
    #     if dimensionIds is None:
    #         raise ValueError("dimensionIds parameters should be used")
    #     if type(dimensionIds) != list:
    #         raise TypeError("dimensionIds should be a list")
    #     if len(dimensionIds)>5:
    #         raise ValueError("dimensionIds should not countain more than 5 elements")
    #     if 'dimension' in self.__request.keys():
    #         del self.__request["dimension"]
    #     self.__request["dimensions"] = dimensionIds

    def removeSearch(self)->None:
        """
        Remove the search capability in the request.
        """
        del self.__request["search"]
        self.search = False

    def setSampling(self, sample: float = None, upsample: bool = False) -> None:
        """
        Set the sampling parameters. Sampling happens at the person level, 
        not at the event level to ensure all events for a person are included.
        Upsampling will multiply the sample results to the full scale of the
        original dataset (assuming the sample is representative).
        Arguments:
            sample : OPTIONAL : A float between 0 and 1 indicating the sample rate.
            upsample : OPTIONAL : A boolean indicating whether to upsample (default is False).
        """
        if sample is not None and (sample < 0 or sample > 1):
            raise ValueError("Sample rate must be between 0 and 1.")
        self.__request["settings"]["sampling"] = sample
        self.__request["settings"]["samplingUpSample"] = upsample

    def setRepeatInstance(self, repeat: bool = True) -> None:
        """
        Specify if repeated instances should be counted.
        Arguments:
            repeat : OPTIONAL : True or False (True by default)
        """
        self.__request["settings"]["countRepeatInstances"] = repeat

    def setNoneBehavior(self, returnNones: bool = True) -> None:
        """
        Set the behavior of the None values in that request.
        Arguments:
            returnNones : OPTIONAL : True or False (True by default)
        """
        if returnNones:
            self.__request["settings"]["nonesBehavior"] = "return-nones"
        else:
            self.__request["settings"]["nonesBehavior"] = "exclude-nones"

    def setDimension(self, dimension: str = None) -> None:
        """
        Set the dimension to be used for reporting.
        Arguments:
            dimension : REQUIRED : the dimension to build your report on
        """
        if dimension is None:
            raise ValueError("A dimension must be passed")
        if 'dimensions' in self.__request.keys():
            del self.__request["dimensions"]
        self.__request["dimension"] = dimension

    def setIdentityOverrides(self, identity_overrides: list) -> None:
        """
        Set the identityOverrides for the request.
        Arguments:
            identity_overrides : REQUIRED : the identityOverrides definition as a list of dictionaries
        """
        if not isinstance(identity_overrides, list):
            raise ValueError("identity_overrides must be a list of dictionaries")
        if not all(isinstance(item, dict) for item in identity_overrides):
            raise ValueError("All items in identity_overrides must be dictionaries")
        
        self.__request["identityOverrides"] = identity_overrides
    
    def setDataViewId(self, dataViewId: str = None) -> None:
        """
        Set the dataView ID to be used for the reporting.
        Arguments:
            dataViewId : REQUIRED : The Data View ID to be passed.
        """
        if dataViewId is None:
            raise ValueError("A dataView ID must be passed")
        self.__request["dataId"] = dataViewId

    def addGlobalFilter(self, filterId: str = None) -> None:
        """
        Add a global filter to the report.
        NOTE : You need to have a dateRange filter at least in the global report.
        Arguments:
            filterId : REQUIRED : The filter to add to the global filter.
                example :
                "s2120430124uf03102jd8021" -> segment
                "2020-01-01T00:00:00.000/2020-02-01T00:00:00.000" -> dateRange
        """
        if filterId.startswith("s") and "@AdobeOrg" in filterId:
            filterType = "segment"
            filter = {
                "type": filterType,
                "segmentId": filterId,
            }
        elif filterId.startswith("20") and "/20" in filterId:
            filterType = "dateRange"
            filter = {
                "type": filterType,
                "dateRange": filterId,
            }
        elif ":::" in filterId:
            filterType = "breakdown"
            dimension, itemId = filterId.split(":::")
            filter = {
                "type": filterType,
                "dimension": dimension,
                "itemId": itemId,
            }
        else:  ### case when it is predefined segments like "All_Visits"
            filterType = "segment"
            filter = {
                "type": filterType,
                "segmentId": filterId,
            }
        ### incrementing the count for globalFilter
        self.__globalFiltersCount += 1
        ### adding to the globalFilter list
        self.__request["globalFilters"].append(filter)

    def updateDateRange(
        self,
        dateRange: str = None,
        shiftingDays: int = None,
        shiftingDaysEnd: int = None,
        shiftingDaysStart: int = None,
    ) -> None:
        """
        Update the dateRange filter on the globalFilter list
        One of the 3 elements specified below is required.
        Arguments:
            dateRange : OPTIONAL : string representing the new dateRange string, such as: 2020-01-01T00:00:00.000/2020-02-01T00:00:00.000
            shiftingDays : OPTIONAL : An integer, if you want to add or remove days from the current dateRange provided. Apply to end and beginning of dateRange.
                So 2020-01-01T00:00:00.000/2020-02-01T00:00:00.000 with +2 will give 2020-01-03T00:00:00.000/2020-02-03T00:00:00.000
            shiftingDaysEnd : : OPTIONAL : An integer, if you want to add or remove days from the last part of the current dateRange. Apply only to end of the dateRange.
                So 2020-01-01T00:00:00.000/2020-02-01T00:00:00.000 with +2 will give 2020-01-01T00:00:00.000/2020-02-03T00:00:00.000
            shiftingDaysStart : OPTIONAL : An integer, if you want to add or remove days from the last first part of the current dateRange. Apply only to beginning of the dateRange.
                So 2020-01-01T00:00:00.000/2020-02-01T00:00:00.000 with +2 will give 2020-01-03T00:00:00.000/2020-02-01T00:00:00.000
        """
        pos = -1
        for index, filter in enumerate(self.__request["globalFilters"]):
            if filter["type"] == "dateRange":
                pos = index
                curDateRange = filter["dateRange"]
                start, end = curDateRange.split("/")
                start = datetime.datetime.fromisoformat(start)
                end = datetime.datetime.fromisoformat(end)
        if dateRange is not None and type(dateRange) == str:
            for index, filter in enumerate(self.__request["globalFilters"]):
                if filter["type"] == "dateRange":
                    pos = index
                    curDateRange = filter["dateRange"]
            newDef = {
                "type": "dateRange",
                "dateRange": dateRange,
            }
        if shiftingDays is not None and type(shiftingDays) == int:
            newStart = (start + datetime.timedelta(shiftingDays)).isoformat(
                timespec="milliseconds"
            )
            newEnd = (end + datetime.timedelta(shiftingDays)).isoformat(
                timespec="milliseconds"
            )
            newDef = {
                "type": "dateRange",
                "dateRange": f"{newStart}/{newEnd}",
            }
        elif shiftingDaysEnd is not None and type(shiftingDaysEnd) == int:
            newEnd = (end + datetime.timedelta(shiftingDaysEnd)).isoformat(
                timespec="milliseconds"
            )
            newDef = {
                "type": "dateRange",
                "dateRange": f"{start}/{newEnd}",
            }
        elif shiftingDaysStart is not None and type(shiftingDaysStart) == int:
            newStart = (start + datetime.timedelta(shiftingDaysStart)).isoformat(
                timespec="milliseconds"
            )
            newDef = {
                "type": "dateRange",
                "dateRange": f"{newStart}/{end}",
            }
        if pos > -1:
            self.__request["globalFilters"][pos] = newDef
        else:  ## in case there is no dateRange already
            self.__request["globalFilters"][pos].append(newDef)

    def removeGlobalFilter(self, index: int = None, filterId: str = None) -> None:
        """
        Remove a specific filter from the globalFilter list.
        You can use either the index of the list or the specific Id of the filter used.
        Arguments:
            index : REQUIRED : index in the list return
            filterId : REQUIRED : the id of the filter to be removed (ex: filterId, dateRange)
        """
        pos = -1
        if index is not None:
            del self.__request["globalFilters"][index]
        elif filterId is not None:
            for index, filter in enumerate(self.__request["globalFilters"]):
                if filterId in str(filter):
                    pos = index
            if pos > -1:
                del self.__request["globalFilters"][pos]
                ### decrementing the count for globalFilter
                self.__globalFiltersCount -= 1

    def to_dict(self) -> None:
        """
        Return the request definition
        """
        return deepcopy(self.__request)

    def save(self, fileName: str = None) -> None:
        """
        save the request definition in a JSON file.
        Argument:
            filename : OPTIONAL : Name of the file. (default cjapy_request_<timestamp>.json)
        """
        fileName = fileName or f"cjapy_request_{int(time())}.json"
        with open(fileName, "w") as f:
            f.write(json.dumps(self.to_dict(), indent=4))
